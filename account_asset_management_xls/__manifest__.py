# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Assets Management Excel reporting',
    'version': '10.0.1.0.1',
    'license': 'AGPL-3',
    'author': "Noviat,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools"
               "10.0/account_asset_management_xls",
    'category': 'Accounting & Finance',
    'depends': ['account_asset_management', 'report_xlsx_helper'],
    'data': [
        'wizard/wiz_account_asset_report.xml',
    ],
    'installable': True,
}
