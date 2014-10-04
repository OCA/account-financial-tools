# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
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
    'version': '2.1',
    'depends': ['account'],
    'author': 'OpenERP & Noviat',
    'description': """
Financial asset management.
===========================

This Module manages the assets owned by a company. It will keep
track of depreciation's occurred on those assets. And it allows to create
accounting entries from the depreciation lines.

The full asset life-cycle is managed (from asset creation to asset removal).

Assets can be created manually as well as automatically
(via the creation of an accounting entry on the asset account).

Excel based reporting is available via the 'account_asset_management_xls'
module (cf. http://odoo.apps.com).

The module contains a large number of functional enhancements compared to
the standard account_asset module from OpenERP/Odoo.

The module in NOT compatible with the standard account_asset module.
    """,
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
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
