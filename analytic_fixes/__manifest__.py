# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name' : 'Analytic Accounting fixes',
    'version': '11.0.0.1.0',
    "author": "Rosen Vladimirov <vladimirov.rosen@gmail.com>, "
              "dXFactory Ltd. <http://www.dxfactory.eu>",
    'website': 'https://github.com/rosenvladimirov/account-financial-tools',
    'category': 'Hidden/Dependency',
    'depends' : ['analytic'],
    'description': """
Add company_id in Analytic tag
    """,
    'data': [
        'views/analytic_account_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
