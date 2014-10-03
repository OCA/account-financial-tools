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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class wiz_account_asset_report(orm.TransientModel):

    _name = 'wiz.account.asset.report'
    _description = 'Financial Assets report'

    _columns = {
        'fiscalyear_id': fields.many2one(
            'account.fiscalyear', 'Fiscal Year', required=True),
        'parent_asset_id': fields.many2one(
            'account.asset.asset', 'Asset Filter',
            domain=[('type', '=', 'view')]),
    }

    def xls_export(self, cr, uid, ids, context=None):
        asset_obj = self.pool.get('account.asset.asset')
        wiz_form = self.browse(cr, uid, ids)[0]
        parent_asset_id = wiz_form.parent_asset_id.id
        if not parent_asset_id:
            parent_ids = asset_obj.search(
                cr, uid, [('type', '=', 'view'), ('parent_id', '=', False)])
            if not parent_ids:
                raise orm.except_orm(
                    _('Configuration Error'),
                    _("No top level asset of type 'view' defined!"))
            else:
                parent_asset_id = parent_ids[0]

        # sanity check
        error_ids = asset_obj.search(
            cr, uid, [('type', '=', 'normal'), ('parent_id', '=', False)])
        for error_id in error_ids:
            error = asset_obj.browse(cr, uid, error_id, context=context)
            error_name = error.name
            if error.code:
                error_name += ' (' + error.code + ')' or ''
            raise orm.except_orm(
                _('Configuration Error'),
                _("No parent asset defined for asset '%s'!") % error_name)

        domain = [('type', '=', 'normal'), ('id', 'child_of', parent_asset_id)]
        asset_ids = asset_obj.search(cr, uid, domain)
        if not asset_ids:
            raise orm.except_orm(
                _('No Data Available'),
                _('No records found for your selection!'))

        datas = {
            'model': 'account.asset.asset',
            'fiscalyear_id': wiz_form.fiscalyear_id.id,
            'ids': [parent_asset_id],
        }
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.asset.xls',
                'datas': datas}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
