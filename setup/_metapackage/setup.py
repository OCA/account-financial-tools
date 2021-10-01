import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-account-financial-tools",
    description="Meta package for oca-account-financial-tools Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-account_asset_batch_compute',
        'odoo13-addon-account_asset_management',
        'odoo13-addon-account_asset_management_menu',
        'odoo13-addon-account_balance_line',
        'odoo13-addon-account_cash_basis_group_base_line',
        'odoo13-addon-account_chart_update',
        'odoo13-addon-account_check_deposit',
        'odoo13-addon-account_fiscal_month',
        'odoo13-addon-account_fiscal_position_allowed_journal',
        'odoo13-addon-account_fiscal_year',
        'odoo13-addon-account_invoice_constraint_chronology',
        'odoo13-addon-account_journal_lock_date',
        'odoo13-addon-account_loan',
        'odoo13-addon-account_lock_date_update',
        'odoo13-addon-account_lock_to_date',
        'odoo13-addon-account_maturity_date_default',
        'odoo13-addon-account_menu',
        'odoo13-addon-account_move_budget',
        'odoo13-addon-account_move_force_removal',
        'odoo13-addon-account_move_line_purchase_info',
        'odoo13-addon-account_move_line_sale_info',
        'odoo13-addon-account_move_line_tax_editable',
        'odoo13-addon-account_move_line_used_currency',
        'odoo13-addon-account_move_print',
        'odoo13-addon-account_move_reversal_choose_method',
        'odoo13-addon-account_move_template',
        'odoo13-addon-account_netting',
        'odoo13-addon-account_spread_cost_revenue',
        'odoo13-addon-account_tax_repartition_line_tax_group_account',
        'odoo13-addon-base_vat_optional_vies',
        'odoo13-addon-product_category_tax',
        'odoo13-addon-stock_account_prepare_anglo_saxon_out_lines_hook',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
