# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Move Line Import',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Noviat,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'category': 'Accounting & Finance',
    'summary': 'Import Accounting Entries',
    'depends': ['account'],
    'data': [
        'views/account_move.xml',
        'wizard/import_move_line_wizard.xml',
    ],
    'installable': True,
}
