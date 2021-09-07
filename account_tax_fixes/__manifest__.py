# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Account tax fixes",
    'version': '11.0.2.0.0',
    'category': 'Accounting',
    "author": "Rosen Vladimirov <vladimirov.rosen@gmail.com>, "
              "dXFactory Ltd. <http://www.dxfactory.eu>",
    'website': 'https://github.com/rosenvladimirov/account-financial-tools',
    'license': 'AGPL-3',
    "depends": [
            'account',
            ],
    'data': [
            'views/account_view.xml',
            'views/account_invoice_view.xml',
    ],
    'installable': True,
}
