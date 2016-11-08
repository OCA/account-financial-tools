# -*- coding: utf-8 -*-
# © 2013-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# © 2016 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Fiscal Position VAT Check',
    'version': '9.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Check VAT on invoice validation',
    'author': "Akretion, "
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com',
    'depends': ['account', 'base_vat'],
    'data': [
        'views/account_fiscal_position_view.xml',
    ],
    'installable': True,
}
