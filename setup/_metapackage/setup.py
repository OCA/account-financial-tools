import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo9-addons-oca-account-financial-tools",
    description="Meta package for oca-account-financial-tools Odoo addons",
    version=version,
    install_requires=[
        'odoo9-addon-account_asset_depr_line_cancel',
        'odoo9-addon-account_balance_line',
        'odoo9-addon-account_chart_update',
        'odoo9-addon-account_check_deposit',
        'odoo9-addon-account_cost_center',
        'odoo9-addon-account_credit_control',
        'odoo9-addon-account_fiscal_position_vat_check',
        'odoo9-addon-account_fiscal_year',
        'odoo9-addon-account_invoice_currency',
        'odoo9-addon-account_invoice_tax_required',
        'odoo9-addon-account_move_line_purchase_info',
        'odoo9-addon-account_move_locking',
        'odoo9-addon-account_permanent_lock_move',
        'odoo9-addon-account_renumber',
        'odoo9-addon-account_reversal',
        'odoo9-addon-currency_rate_update',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 9.0',
    ]
)
