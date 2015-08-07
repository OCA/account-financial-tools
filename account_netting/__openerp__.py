# -*- coding: utf-8 -*-
# (c) 2015 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Account netting',
    'version': '8.0.1.0.0',
    'summary': "Compensate AR/AP accounts from the same partner",
    'category': 'Accounting & Finance',
    'author': 'Serv. Tecnol. Avanzados - Pedro M. Baeza, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account',
    ],
    'data': [
        'wizard/account_move_make_netting_view.xml',
    ],
    "installable": True,
}
