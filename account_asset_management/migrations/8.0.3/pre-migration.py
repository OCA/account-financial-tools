# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

column_renames = {
    'account_account': [
        ('asset_category_id', 'asset_profile_id', 'Asset Profile'),
    ],
    'account_asset': [
        ('asset_value', 'depreciation_base', 'Depreciation Base'),
        ('category_id', 'profile_id', 'Asset Profile'),
    ],
    'account_invoice_line': [
        ('asset_category_id', 'asset_profile_id', 'Asset Profile'),
    ],
    'account_move_line': [
        ('asset_category_id', 'asset_profile_id', 'Asset Profile'),
    ],
}

table_renames = [
    ('account_asset_asset', 'account_asset'),
    ('account_asset_category', 'account_asset_profile'),
    ('account_asset_depreciation_line', 'account_asset_line')]

model_renames = [
    ('account.asset.asset', 'account.asset'),
    ('account.asset.category', 'account.asset.profile'),
    ('account.asset.depreciation.line', 'account.asset.line')]

view_refs = [
    'account_asset_management.view_account_asset_form',
    'account_asset_management.view_invoice_asset_category',
    'account_asset_management.view_account_invoice_asset_form',
    'account_asset_management.view_account_move_line_form_inherit',
    'account_asset_management.view_account_move_asset_form'
]


def is_module_installed(cr, module):
    """ Check if `module` is installed.
    :return: True / False
    """
    cr.execute(
        "SELECT id FROM ir_module_module "
        "WHERE name=%s and state IN ('installed', 'to upgrade')", (module,))
    return bool(cr.fetchone())


def table_exists(cr, table):
    """ Check whether a certain table or view exists """
    cr.execute('SELECT 1 FROM pg_class WHERE relname = %s', (table,))
    return cr.fetchone()


def rename_columns(cr, column_spec):
    for table in column_spec.keys():
        for (old, new, comment) in column_spec[table]:
            cr.execute(
                "SELECT column_name "
                "FROM information_schema.columns "
                "WHERE table_name=%s "
                "AND column_name=%s",
                (table, new))
            res = cr.fetchone()
            if not res:
                _logger.info("table %s, column %s: renaming to %s",
                             table, old, new)
                cr.execute(
                    'ALTER TABLE "%s" RENAME "%s" TO "%s"'
                    % (table, old, new,))
                cr.execute('DROP INDEX IF EXISTS "%s_%s_index"' % (table, old))
                if comment:
                    cr.execute(
                        "COMMENT ON COLUMN %s.%s IS '%s'"
                        % (table, new, comment))


def rename_tables(cr, table_spec):
    to_rename = [x[0] for x in table_spec]
    for old, new in list(table_spec):
        if (table_exists(cr, old + '_id_seq') and
                old + '_id_seq' not in to_rename):
            table_spec.append((old + '_id_seq', new + '_id_seq'))
    for (old, new) in table_spec:
        _logger.info("table %s: renaming to %s",
                     old, new)
        if table_exists(cr, old) and not table_exists(cr, new):
            cr.execute('ALTER TABLE "%s" RENAME TO "%s"' % (old, new))


def rename_models(cr, model_spec):
    for (old, new) in model_spec:
        _logger.info("model %s: renaming to %s",
                     old, new)
        cr.execute('UPDATE ir_model SET model = %s '
                   'WHERE model = %s', (new, old,))
        cr.execute('UPDATE ir_model_fields SET relation = %s '
                   'WHERE relation = %s', (new, old,))
        cr.execute('UPDATE ir_model_data SET model = %s '
                   'WHERE model = %s', (new, old,))
        cr.execute('UPDATE ir_attachment SET res_model = %s '
                   'WHERE res_model = %s', (new, old,))
        cr.execute('UPDATE ir_model_fields SET model = %s '
                   'WHERE model = %s', (new, old,))
        cr.execute('UPDATE ir_translation set '
                   "name=%s || substr(name, strpos(name, ',')) "
                   'where name like %s',
                   (new, old + ',%'),)
        if is_module_installed(cr, 'mail'):
            # fortunately, the data model didn't change up to now
            cr.execute(
                'UPDATE mail_message SET model=%s where model=%s', (new, old),
            )
            if table_exists(cr, 'mail_followers'):
                cr.execute(
                    'UPDATE mail_followers SET res_model=%s '
                    'WHERE res_model=%s',
                    (new, old),
                )


def remove_views(cr, view_refs):
    model = 'ir.ui.view'
    for view_ref in view_refs:
        module, name = view_ref.split('.')
        cr.execute(
            'SELECT res_id FROM ir_model_data '
            'WHERE module = %s AND name = %s AND model = %s',
            (module, name, model)
        )
        res = cr.fetchone()
        if res:
            cr.execute(
                'DELETE FROM ir_ui_view WHERE id = %s', (res[0],))


def migrate(cr, version):
    remove_views(cr, view_refs)
    rename_tables(cr, table_renames)
    rename_models(cr, model_renames)
    rename_columns(cr, column_renames)
