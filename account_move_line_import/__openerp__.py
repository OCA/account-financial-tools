# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Account Move Line Import',
    'version': '8.0.1.0.2',
    'license': 'AGPL-3',
    'author': 'Noviat,'
              'Odoo Community Association (OCA)',
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'summary': 'Import Accounting Entries',
    'depends': ['account'],
    'data': [
        'views/account_move.xml',
        'wizard/import_move_line_wizard.xml',
    ],
    'demo': [
        'demo/account_move.xml',
    ],
    'installable': True,
}
