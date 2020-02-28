# Copyright 2019 Apps2GROW - Henrik Norlin
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
from psycopg2 import sql


def create_asset_groups(cr):
    # Add a supporting column for indicating the source asset view
    origin_column = sql.Identifier(
        openupgrade.get_legacy_name('view_asset_id'))
    openupgrade.logged_query(
        cr, sql.SQL("ALTER TABLE account_asset_group ADD {} int4").format(
            origin_column,
        ),
    )
    # Now fill new table recursively attending parents
    parent_column = sql.Identifier(openupgrade.get_legacy_name('parent_id'))
    parent_group_ids = ('NULL', )
    query_sql = sql.SQL("""
        INSERT INTO account_asset_group (
            name, code, company_id, parent_id, create_uid,
            create_date, write_date, write_uid, {origin_column}
        )
        SELECT va.name, va.code, va.company_id, aag2.id, va.create_uid,
            va.create_date, va.write_date, va.write_uid, va.id
        FROM {table} va
        LEFT JOIN account_asset_group aag2
            ON aag2.{origin_column} = va.{parent_column}
        WHERE {parent_column} {rest_sql}
        RETURNING id
    """)
    isnull = sql.SQL("IS NULL")
    inids = sql.SQL("IN %(ids)s")
    while parent_group_ids:
        query = query_sql.format(
            origin_column=origin_column,
            table=sql.Identifier(
                openupgrade.get_legacy_name('account_asset_view')
            ),
            parent_column=parent_column,
            rest_sql=isnull if parent_group_ids == ('NULL', ) else inids
        )
        openupgrade.logged_query(cr, query, {'ids': parent_group_ids})
        parent_group_ids = tuple(x[0] for x in cr.fetchall())


def update_asset_group_links(cr):
    parent_column = sql.Identifier(openupgrade.get_legacy_name('parent_id'))
    origin_column = sql.Identifier(
        openupgrade.get_legacy_name('view_asset_id'))
    openupgrade.logged_query(
        cr, sql.SQL("""
        INSERT INTO account_asset_profile_group_rel
        (profile_id, group_id)
        SELECT aap.id, aag.id
        FROM account_asset_profile aap
        JOIN account_asset_group aag
            ON aag.{origin_column} = aap.{parent_column}""").format(
            parent_column=parent_column,
            origin_column=origin_column,
        ),
    )
    openupgrade.logged_query(
        cr, sql.SQL("""
        INSERT INTO account_asset_group_rel
        (asset_id, group_id)
        SELECT aa.id, aag.id
        FROM account_asset aa
        JOIN account_asset_group aag
            ON aag.{origin_column} = aa.{parent_column}""").format(
            parent_column=parent_column,
            origin_column=origin_column,
        ),
    )


@openupgrade.migrate()
def migrate(env, version):
    column = openupgrade.get_legacy_name('parent_id')
    if openupgrade.column_exists(env.cr, 'account_asset_profile', column):
        # if migrating directly from v11 `account_asset` module, there are no
        # view assets nor parents
        create_asset_groups(env.cr)
        update_asset_group_links(env.cr)
