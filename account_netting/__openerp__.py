# -*- coding: utf-8 -*-
# (c) 2015 Pedro M. Baeza
# (c) 2016 Noviat nv/sa (www.noviat.com)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Account netting',
    'version': '8.0.2.0.0',
    'license': 'AGPL-3',
    'summary': "Compensate AR/AP accounts from the same partner",
    'category': 'Accounting & Finance',
    'author': 'Tecnativa - Pedro M. Baeza, '
              'Noviat, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account',
    ],
    'data': [
        'demo/account_netting_demo.xml',
        'wizard/account_move_make_netting_view.xml',
    ],
    "installable": True,
}
