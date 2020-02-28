# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
from psycopg2 import sql


_column_renames = {
    'account_asset_profile': [
        ('parent_id', None),
    ],
    'account_asset': [
        ('parent_id', None),
    ],
}


def move_view_assets(cr):
    """Copy view assets to other table for preserving them, but outside of the
    main table, so remove them from there.
    """
    temp_table = sql.Identifier(
        openupgrade.get_legacy_name('account_asset_view'))
    openupgrade.logged_query(
        cr, sql.SQL("""
        CREATE TABLE {} AS (
            SELECT * FROM account_asset
            WHERE type='view'
        )""").format(temp_table),
    )
    openupgrade.logged_query(cr, "DELETE FROM account_asset WHERE type='view'")


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, 'account_asset_profile', 'parent_id'):
        # if migrating directly from v11 `account_asset` module, there are no
        # view assets nor parents
        openupgrade.rename_columns(env.cr, _column_renames)
        openupgrade.logged_query(
            env.cr, """
            ALTER TABLE account_asset
            DROP CONSTRAINT account_asset_parent_id_fkey""",
        )
        openupgrade.logged_query(
            env.cr, """
            ALTER TABLE account_asset_profile
            DROP CONSTRAINT account_asset_profile_parent_id_fkey""",
        )
        move_view_assets(env.cr)
