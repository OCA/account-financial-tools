# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Currency Monthly Rate",
    "version": "11.0.1.0.0",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Generic Modules/Accounting",
    "description": """Use monthly currency rate average""",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ['base'],
    "data": [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/res_currency.xml',
    ],
    'installable': True,
}
