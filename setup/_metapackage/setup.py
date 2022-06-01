import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-account-financial-tools",
    description="Meta package for oca-account-financial-tools Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-account_asset_batch_compute',
        'odoo14-addon-account_asset_management',
        'odoo14-addon-account_asset_management_menu',
        'odoo14-addon-account_asset_number',
        'odoo14-addon-account_asset_transfer',
        'odoo14-addon-account_balance_line',
        'odoo14-addon-account_cash_deposit',
        'odoo14-addon-account_chart_update',
        'odoo14-addon-account_check_deposit',
        'odoo14-addon-account_fiscal_month',
        'odoo14-addon-account_fiscal_position_vat_check',
        'odoo14-addon-account_fiscal_year',
        'odoo14-addon-account_invoice_constraint_chronology',
        'odoo14-addon-account_journal_general_sequence',
        'odoo14-addon-account_journal_lock_date',
        'odoo14-addon-account_loan',
        'odoo14-addon-account_lock_date_update',
        'odoo14-addon-account_lock_to_date',
        'odoo14-addon-account_menu',
        'odoo14-addon-account_move_budget',
        'odoo14-addon-account_move_fiscal_month',
        'odoo14-addon-account_move_fiscal_year',
        'odoo14-addon-account_move_force_removal',
        'odoo14-addon-account_move_line_menu',
        'odoo14-addon-account_move_line_purchase_info',
        'odoo14-addon-account_move_line_sale_info',
        'odoo14-addon-account_move_line_tax_editable',
        'odoo14-addon-account_move_name_sequence',
        'odoo14-addon-account_move_print',
        'odoo14-addon-account_move_template',
        'odoo14-addon-account_netting',
        'odoo14-addon-account_no_default',
        'odoo14-addon-account_sequence_option',
        'odoo14-addon-account_template_active',
        'odoo14-addon-base_vat_optional_vies',
        'odoo14-addon-product_category_tax',
        'odoo14-addon-stock_account_prepare_anglo_saxon_out_lines_hook',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
