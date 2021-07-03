import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-account-financial-tools",
    description="Meta package for oca-account-financial-tools Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-account_asset_disposal',
        'odoo11-addon-account_asset_management',
        'odoo11-addon-account_balance_line',
        'odoo11-addon-account_chart_update',
        'odoo11-addon-account_check_deposit',
        'odoo11-addon-account_cost_center',
        'odoo11-addon-account_credit_control',
        'odoo11-addon-account_credit_control_dunning_fees',
        'odoo11-addon-account_document_reversal',
        'odoo11-addon-account_fiscal_month',
        'odoo11-addon-account_fiscal_position_vat_check',
        'odoo11-addon-account_fiscal_year',
        'odoo11-addon-account_group_menu',
        'odoo11-addon-account_invoice_constraint_chronology',
        'odoo11-addon-account_invoice_currency',
        'odoo11-addon-account_journal_lock_date',
        'odoo11-addon-account_loan',
        'odoo11-addon-account_lock_date_update',
        'odoo11-addon-account_lock_to_date',
        'odoo11-addon-account_move_batch_validate',
        'odoo11-addon-account_move_budget',
        'odoo11-addon-account_move_fiscal_month',
        'odoo11-addon-account_move_fiscal_year',
        'odoo11-addon-account_move_line_purchase_info',
        'odoo11-addon-account_move_line_tax_editable',
        'odoo11-addon-account_move_template',
        'odoo11-addon-account_netting',
        'odoo11-addon-account_partner_required',
        'odoo11-addon-account_permanent_lock_move',
        'odoo11-addon-account_renumber',
        'odoo11-addon-account_reversal',
        'odoo11-addon-account_spread_cost_revenue',
        'odoo11-addon-account_tag_menu',
        'odoo11-addon-account_type_menu',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
