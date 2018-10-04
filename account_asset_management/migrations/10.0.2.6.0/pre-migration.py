# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2011-2013 Therp BV (<http://therp.nl>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# Migration scripts based on OpenUpgrade

import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

column_renames = {
    'account_asset': [
        ('asset_value', 'depreciation_base'),
        ('category_id', 'profile_id'),
    ],
    'account_account': [
        ('asset_category_id', 'asset_profile_id'),
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
        for (old, new) in column_spec[table]:
            _logger.info("table %s, column %s: renaming to %s",
                         table, old, new)
            cr.execute(
                'ALTER TABLE "%s" RENAME "%s" TO "%s"' % (table, old, new,))
            cr.execute('DROP INDEX IF EXISTS "%s_%s_index"' % (table, old))


def rename_tables(cr, table_spec):
    to_rename = [x[0] for x in table_spec]
    for old, new in list(table_spec):
        if (table_exists(cr, old + '_id_seq') and
                old + '_id_seq' not in to_rename):
            table_spec.append((old + '_id_seq', new + '_id_seq'))
    for (old, new) in table_spec:
        _logger.info("table %s: renaming to %s",
                     old, new)
        cr.execute('ALTER TABLE "%s" RENAME TO "%s"' % (old, new,))


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
                    'where res_model=%s',
                    (new, old),
                )


def migrate(cr, version):
    rename_tables(cr, table_renames)
    rename_models(cr, model_renames)
    rename_columns(cr, column_renames)
