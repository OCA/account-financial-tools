# -*- coding: utf-8 -*-
# Copyright 2014 Noviat nv/sa (www.noviat.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Assets Management Excel reporting',
    'version': '8.0.0.1.0',
    'license': 'AGPL-3',
    'author': "Noviat,Odoo Community Association (OCA)",
    'category': 'Accounting & Finance',
    'depends': ['account_asset_management', 'report_xls'],
    'data': [
        'wizard/account_asset_report_wizard.xml',
    ],
    'installable': True,
}
