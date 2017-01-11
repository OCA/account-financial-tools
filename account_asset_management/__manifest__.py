# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2014-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Assets Management',
    'version': '10.0.2.6.0',
    'depends': ['account', 'account_fiscal_year'],
    'conflicts': ['account_asset'],
    'author': "OpenERP & Noviat,Odoo Community Association (OCA)",
    'website': 'http://www.noviat.com',
    'category': 'Accounting & Finance',
    'sequence': 32,
    'test': [
#        'test/account_asset_demo.yml',
#        'test/account_asset.yml',
    ],
    'data': [
        'security/account_asset_security.xml',
        'security/ir.model.access.csv',
        'views/account_asset_view.xml',
        'views/account_account.xml',
        'views/account_invoice.xml',
#        'report/account_asset_report_view.xml',
        'views/res_config_view.xml',
        'wizard/wizard_asset_compute_view.xml',
        'wizard/account_asset_remove_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
