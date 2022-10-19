import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-account-financial-tools",
    description="Meta package for oca-account-financial-tools Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-account_fiscal_year>=16.0dev,<16.1dev',
        'odoo-addon-account_invoice_constraint_chronology>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
