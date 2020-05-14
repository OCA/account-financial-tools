# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Account Move Transfers",
    'version': '11.0.4.0.0',
    'category': 'Generic Modules/Accounting',
    'summary': "Transfer saldo to other account inside movement in Journal Entries",
    'author': "Rosen Vladimirov, "
              "dXFactory Ltd.",
    'website': 'https://github.com/rosenvladimirov/account-financial-tools',
    'license': 'AGPL-3',
    'depends': ['account', 'analytic'],
    'data': [
        'wizard/create_transfer.xml',
        'views/account_view.xml',
    ],
    'test': [
    ],
    'installable': True,
}
