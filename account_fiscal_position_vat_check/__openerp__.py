# -*- coding: utf-8 -*-
# © 2013-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Fiscal Position VAT Check',
    'version': '8.0.0.1.2',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Check VAT on invoice validation',
    'author': "Akretion,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com',
    'depends': ['account', 'base_vat'],
    'data': [
        'account_fiscal_position_view.xml',
    ],
    'installable': True,
}
