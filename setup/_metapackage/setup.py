import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-account-financial-tools",
    description="Meta package for oca-account-financial-tools Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-account_asset_management',
        'odoo14-addon-account_balance_line',
        'odoo14-addon-account_fiscal_position_vat_check',
        'odoo14-addon-account_fiscal_year',
        'odoo14-addon-account_menu',
        'odoo14-addon-account_move_line_menu',
        'odoo14-addon-account_move_line_tax_editable',
        'odoo14-addon-account_move_template',
        'odoo14-addon-account_no_default',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
