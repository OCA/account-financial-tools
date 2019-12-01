# Copyright 2019 Apps2GROW - Henrik Norlin
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_model_renames = [
    ('account.asset.category', 'account.asset.profile'),
    ('account.asset.depreciation.line', 'account.asset.line'),
    ('account.asset.asset', 'account.asset'),
]

_table_renames = [
    (old.replace('.', '_'), new.replace('.', '_'))
    for (old, new) in _model_renames
]

_column_copies = {
    'account_asset': [
        ('method_number', None, None),
        ('method_time', None, None),
    ],
    'account_asset_profile': [
        ('method_number', None, None),
        ('method_time', None, None),
    ],
}

_column_renames = {
    'account_asset': [
        ('method_period', None),
    ],
    'account_asset_profile': [
        ('method_period', None),
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


def handle_account_asset_disposal_migration(env):
    """Take care of potentially installed `account_asset_disposal` module.

    In this phase we rename stuff for adapting to the new data structure.
    """
    cr = env.cr
    if not openupgrade.column_exists(cr, 'account_asset', 'disposal_move_id'):
        return
    openupgrade.copy_columns(cr, {'account_asset': [('state', None, None)]})
    openupgrade.rename_columns(
        cr, {'account_asset': [('disposal_move_id', None)]})
    openupgrade.map_values(
        cr, openupgrade.get_legacy_name('state'), 'state',
        [('disposed', 'removed')], table='account_asset',
    )
    openupgrade.rename_fields(
        env, [
            ('account.asset', 'account_asset', 'disposal_date', 'date_remove'),
            ('account.asset.profile', 'account_asset_profile',
             'account_loss_id', 'account_residual_value_id'),
        ],
    )


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    if openupgrade.table_exists(cr, 'account_asset_asset'):
        # `account_asset` module was installed in v11
        if openupgrade.table_exists(cr, 'account_asset'):
            # `account_asset_management` module also installed in v11
            # TODO: Merge in existing tables assets if both module installed
            pass
        else:
            openupgrade.rename_models(cr, _model_renames)
            openupgrade.rename_tables(cr, _table_renames)
            openupgrade.copy_columns(cr, _column_copies)
            openupgrade.rename_columns(cr, _column_renames)
            openupgrade.rename_fields(env, _field_renames)
            handle_account_asset_disposal_migration(env)
            if openupgrade.column_exists(cr, 'account_asset',
                                         'analytic_account_id'):
                # account_asset_analytic module in OCA/account_analytic
                openupgrade.rename_fields(
                    env, [('account.asset', 'account_asset',
                           'analytic_account_id', 'account_analytic_id')])
