# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
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
    'name': 'Assets Management Excel reporting',
    'version': '8.0.0.1.0',
    'license': 'AGPL-3',
    'author': "Noviat,Odoo Community Association (OCA)",
    'category': 'Accounting & Finance',
    'description': """
Assets Management Excel reporting
---------------------------------

This module adds Excel reporting to Financial Assets Management Module.

Assistance
----------

Contact info@noviat.com if you require support or functional extensions
for this module.

    """,
    'depends': ['account_asset_management', 'report_xls'],
    'data': [
        'wizard/account_asset_report_wizard.xml',
    ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
