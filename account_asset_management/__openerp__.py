# -*- coding: utf-8 -*-
# Copyright 2010-2012 OpenERP s.a. (<http://openerp.com>).
# Copyright 2014-2015 Noviat nv/sa (www.noviat.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Assets Management',
    'version': '8.0.2.6.0',
    'depends': ['account'],
    'conflicts': ['account_asset'],
    'author': "OpenERP & Noviat,Odoo Community Association (OCA)",
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'sequence': 32,
    'demo': ['account_asset_demo.xml'],
    'test': [
        'test/account_asset_demo.yml',
        'test/account_asset.yml',
    ],
    'data': [
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'wizard/account_asset_change_duration_view.xml',
        'wizard/wizard_asset_compute_view.xml',
        'wizard/account_asset_remove_view.xml',
        'account_asset_view.xml',
        'account_view.xml',
        'account_asset_invoice_view.xml',
        'report/account_asset_report_view.xml',
        'res_config_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}
