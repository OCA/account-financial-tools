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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm


class account_asset_asset(orm.Model):
    _inherit = 'account.asset.asset'

    def _xls_acquisition_fields(self, cr, uid, context=None):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            'account', 'name', 'code', 'date_start', 'asset_value',
            'salvage_value',
        ]

    def _xls_active_fields(self, cr, uid, context=None):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            'account', 'name', 'code', 'date_start',
            'asset_value', 'salvage_value',
            'fy_start_value', 'fy_depr', 'fy_end_value',
            'fy_end_depr',
            'method', 'method_number', 'prorata',
        ]

    def _xls_removal_fields(self, cr, uid, context=None):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            'account', 'name', 'code', 'date_remove', 'asset_value',
            'salvage_value',
        ]

    def _xls_acquisition_template(self, cr, uid, context=None):
        """
        Template updates

        """
        return {}

    def _xls_active_template(self, cr, uid, context=None):
        """
        Template updates

        """
        return {}

    def _xls_removal_template(self, cr, uid, context=None):
        """
        Template updates

        """
        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
