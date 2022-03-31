import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-account-financial-tools",
    description="Meta package for oca-account-financial-tools Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-account_invoice_constraint_chronology>=15.0dev,<15.1dev',
        'odoo-addon-account_move_line_purchase_info>=15.0dev,<15.1dev',
        'odoo-addon-account_move_line_sale_info>=15.0dev,<15.1dev',
        'odoo-addon-base_vat_optional_vies>=15.0dev,<15.1dev',
        'odoo-addon-product_category_tax>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
