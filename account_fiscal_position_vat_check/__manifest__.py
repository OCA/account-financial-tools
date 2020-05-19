# Copyright 2013-2019 Akretion France (https://akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Fiscal Position VAT Check',
    'version': '12.0.1.0.0',
    'category': 'Invoices & Payments',
    'license': 'AGPL-3',
    'summary': 'Check VAT on invoice validation',
    'author': "Akretion,Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': ['account', 'base_vat'],
    'data': [
        'views/account_fiscal_position.xml',
    ],
    'installable': True,
}
