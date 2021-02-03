# Copyright 2009-2019 Noviat
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Assets Management',
    'version': '12.0.3.0.0',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'report_xlsx_helper',
    ],
    'excludes': ['account_asset'],
    'author': "Noviat,Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/account-financial-tools',
    'category': 'Accounting & Finance',
    'data': [
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'report/account_asset_report_views.xml',
        'wizard/account_asset_compute.xml',
        'wizard/account_asset_remove.xml',
        'views/account_account.xml',
        'views/account_asset.xml',
        'views/account_asset_group.xml',
        'views/account_asset_profile.xml',
        'views/res_config_settings.xml',
        'views/account_invoice.xml',
        'views/account_invoice_line.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/menuitem.xml',
        'wizard/wiz_account_asset_report.xml',
    ],
}
