# -*- coding: utf-8 -*-
# © 2015 Eficent
# © 2015 Techrifiv Solutions Pte Ltd
# © 2015 Statecraft Systems Pte Ltd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Invoice - Change Currency',
    'version': '10.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': 'Allows to change currency of Invoice by wizard',
    'author': 'Eficent,Odoo Community Association (OCA)',
    'website': 'http://www.eficent.com',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'wizard/wizard_update_invoice_currency.xml',
        'views/account_invoice_view.xml',
    ],
    'test': [],
    "installable": True
}
