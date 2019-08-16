# Copyright 2019 Apps2GROW - Henrik Norlin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_model_renames1 = [
    ('account.asset.category', 'account.asset.profile'),
    ('account.asset.depreciation.line', 'account.asset.line'),
]

_table_renames1 = [
    (old.replace('.', '_'), new.replace('.', '_'))
    for (old, new) in _model_renames1
]

_model_renames2 = [
    ('account.asset.asset', 'account.asset'),
]

_table_renames2 = [
    (old.replace('.', '_'), new.replace('.', '_'))
    for (old, new) in _model_renames2
]

_column_copies = {
    'account_asset': [
        ('method_number', None, None),
        ('method_period', None, None),
    ],
    'account_asset_profile': [
        ('method_number', None, None),
        ('method_period', None, None),
    ],
}

_field_renames = [
    ('account.asset', 'account_asset', 'category_id', 'profile_id'),
    ('account.asset', 'account_asset', 'currency_id', 'company_currency_id'),
    ('account.asset', 'account_asset', 'date', 'date_start'),
    ('account.asset', 'account_asset', 'value', 'purchase_value'),
    ('account.asset.line', 'account_asset_line',
        'depreciation_date', 'line_date'),
    ('account.asset.profile', 'account_asset_profile',
        'account_depreciation_expense_id', 'account_expense_depreciation_id'),
    ('account.invoice.line', 'account_invoice_line',
        'asset_category_id', 'asset_profile_id'),
]


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    openupgrade.rename_models(cr, _model_renames1)
    openupgrade.rename_tables(cr, _table_renames1)
    openupgrade.rename_models(cr, _model_renames2)
    openupgrade.rename_tables(cr, _table_renames2)
    openupgrade.copy_columns(cr, _column_copies)
    openupgrade.rename_fields(env, _field_renames)
