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
import logging
_logger = logging.getLogger(__name__)


class account_asset_remove(orm.TransientModel):
    _name = 'account.asset.remove'
    _description = 'Remove Asset'

    _columns = {
        'date_remove': fields.date('Asset Removal Date', required=True),
        'period_id': fields.many2one(
            'account.period', 'Force Period',
            domain=[('state', '<>', 'done')],
            help="Keep empty to use the period of the removal ate."),
        'note': fields.text('Notes'),
    }

    def remove(self, cr, uid, ids, context=None):
        asset_obj = self.pool.get('account.asset.asset')
        asset_line_obj = self.pool.get('account.asset.depreciation.line')
        move_line_obj = self.pool.get('account.move.line')
        move_obj = self.pool.get('account.move')
        period_obj = self.pool.get('account.period')

        wiz_data = self.browse(cr, uid, ids[0], context=context)
        asset_id = context['active_id']
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        ctx = dict(context, company_id=asset.company_id.id)
        period_id = wiz_data.period_id and wiz_data.period_id.id or False
        if not period_id:
            ctx.update(account_period_prefer_normal=True)
            period_ids = period_obj.find(
                cr, uid, wiz_data.date_remove, context=ctx)
            period_id = period_ids[0]
        dl_ids = asset_line_obj.search(
            cr, uid,
            [('asset_id', '=', asset.id), ('type', '=', 'depreciate')],
            order='line_date desc')
        last_date = asset_line_obj.browse(cr, uid, dl_ids[0]).line_date
        if wiz_data.date_remove < last_date:
            raise orm.except_orm(
                _('Error!'),
                _("The removal date must be after "
                  "the last depreciation date."))

        line_name = asset_obj._get_depreciation_entry_name(
            cr, uid, asset, len(dl_ids) + 1, context=context)
        journal_id = asset.category_id.journal_id.id

        # create move
        move_vals = {
            'name': asset.name,
            'date': wiz_data.date_remove,
            'ref': line_name,
            'period_id': period_id,
            'journal_id': journal_id,
            'narration': wiz_data.note,
            }
        move_id = move_obj.create(cr, uid, move_vals, context=context)
        partner_id = asset.partner_id and asset.partner_id.id or False
        move_line_obj.create(cr, uid, {
            'name': asset.name,
            'ref': line_name,
            'move_id': move_id,
            'account_id': asset.category_id.account_depreciation_id.id,
            'debit': asset.asset_value > 0 and asset.asset_value or 0.0,
            'credit': asset.asset_value < 0 and -asset.asset_value or 0.0,
            'period_id': period_id,
            'journal_id': journal_id,
            'partner_id': partner_id,
            'date': wiz_data.date_remove,
            'asset_id': asset.id
        }, context={'allow_asset': True})
        move_line_obj.create(cr, uid, {
            'name': asset.name,
            'ref': line_name,
            'move_id': move_id,
            'account_id': asset.category_id.account_asset_id.id,
            'debit': asset.asset_value < 0 and -asset.asset_value or 0.0,
            'credit': asset.asset_value > 0 and asset.asset_value or 0.0,
            'period_id': period_id,
            'journal_id': journal_id,
            'partner_id': partner_id,
            'date': wiz_data.date_remove,
            'asset_id': asset.id
        }, context={'allow_asset': True})

        # create asset line
        asset_line_vals = {
            'amount': asset.asset_value,
            'asset_id': asset_id,
            'name': line_name,
            'line_date': wiz_data.date_remove,
            'move_id': move_id,
            'type': 'remove',
        }
        asset_line_obj.create(cr, uid, asset_line_vals, context=context)
        asset.write({'state': 'removed', 'date_remove': wiz_data.date_remove})

        return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
