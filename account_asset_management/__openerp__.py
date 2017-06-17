# -*- coding: utf-8 -*-
# Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Assets Management',
    'version': '8.0.2.8.0',
    'license': 'AGPL-3',
    'depends': ['account'],
    'conflicts': ['account_asset'],
    'author': "OpenERP & Noviat,Odoo Community Association (OCA)",
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'sequence': 32,
    'demo': ['demo/account_asset_demo.xml'],
    'test': [
        'test/account_asset_demo.yml',
        'test/account_asset.yml',
    ],
    'data': [
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'wizard/account_asset_change_duration.xml',
        'wizard/wizard_asset_compute.xml',
        'wizard/account_asset_remove.xml',
        'views/account_account.xml',
        'views/account_asset_asset.xml',
        'views/account_asset_category.xml',
        'views/account_asset_history.xml',
        'views/account_config_settings.xml',
        'views/account_invoice.xml',
        'views/account_invoice_line.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/menuitem.xml',
        'report/account_asset_report_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
