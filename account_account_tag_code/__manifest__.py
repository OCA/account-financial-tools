# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'account tag code',
    'version': '10.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': """
        Add 'code' field to account tags
    """,
    'author': 'Noviat,'
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_account_tag.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
}
