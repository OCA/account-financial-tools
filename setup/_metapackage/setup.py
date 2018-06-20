import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo11-addons-oca-account-financial-tools",
    description="Meta package for oca-account-financial-tools Odoo addons",
    version=version,
    install_requires=[
        'odoo11-addon-account_balance_line',
        'odoo11-addon-account_credit_control',
        'odoo11-addon-account_credit_control_dunning_fees',
        'odoo11-addon-account_fiscal_year',
        'odoo11-addon-account_group_menu',
        'odoo11-addon-account_invoice_constraint_chronology',
        'odoo11-addon-account_invoice_currency',
        'odoo11-addon-account_loan',
        'odoo11-addon-account_move_fiscal_year',
        'odoo11-addon-account_move_line_tax_editable',
        'odoo11-addon-account_partner_required',
        'odoo11-addon-account_reversal',
        'odoo11-addon-account_tag_menu',
        'odoo11-addon-account_type_menu',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
