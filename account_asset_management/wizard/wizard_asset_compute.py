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

from openerp.osv import fields, orm
from openerp.tools.translate import _


class asset_depreciation_confirmation_wizard(orm.TransientModel):
    _name = "asset.depreciation.confirmation.wizard"
    _description = "asset.depreciation.confirmation.wizard"
    _columns = {
        'period_id': fields.many2one(
            'account.period', 'Period',
            domain="[('special', '=', False), ('state', '=', 'draft')]",
            required=True,
            help="Choose the period for which you want to automatically "
                 "post the depreciation lines of running assets"),
    }

    def _get_period(self, cr, uid, context=None):
        ctx = dict(context or {}, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        if periods:
            return periods[0]
        return False

    _defaults = {
        'period_id': _get_period,
    }

    def asset_compute(self, cr, uid, ids, context):
        ass_obj = self.pool.get('account.asset.asset')
        asset_ids = ass_obj.search(
            cr, uid,
            [('state', '=', 'open'), ('type', '=', 'normal')],
            context=context)
        data = self.browse(cr, uid, ids, context=context)
        period_id = data[0].period_id.id
        created_move_ids = ass_obj._compute_entries(
            cr, uid, asset_ids, period_id,
            check_triggers=True, context=context)
        domain = "[('id', 'in', [" + \
            ','.join(map(str, created_move_ids)) + "])]"
        return {
            'name': _('Created Asset Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'domain': domain,
            'type': 'ir.actions.act_window',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
