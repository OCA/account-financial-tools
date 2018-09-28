# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Fixed Assets import',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': "Noviat,Odoo Community Association (OCA)",
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'depends': [
        'account_asset_management',
    ],
    'data': [
        'wizard/fixed_asset_import.xml'
    ],
    'installable': True,
}
