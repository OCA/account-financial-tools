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

import time
from lxml import etree
from openerp.osv import fields, orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta
from datetime import datetime

class account_asset_revaluation(orm.Model):
    _name = 'account.asset.revaluation'
    _description = 'Revaluate Asset'
    
    _columns = {
        'previous_date_revaluation': fields.date('Date', required=True),
        'date_revaluation': fields.date('Date', required=True),
        'depr_id': fields.many2one('account.asset.depreciation.line', 'Asset depreciation line',
            required=True, ondelete='cascade'),
        'asset_id': fields.many2one('account.asset.asset', 'Asset',
            required=True, ondelete='cascade'),
        'previous_value': fields.float('Old Value', required=True),
        'previous_value_residual': fields.float('Old Value Residual', required=True),
        'revaluated_value': fields.float('New Value', required=True),
        'account_revaluation_id': fields.many2one(
            'account.account', 'Revaluation Value Account',
            domain=[('type', '<>', 'view')], required=True, store=False),
        'note': fields.text('Notes'),
    }
    
    

class account_asset_revaluation(orm.TransientModel):
    _name = 'account.asset.revaluation.wizard'
    _description = 'Revaluate Asset Wizard'
    
    def _get_previous_date_revaluation(self, cr, uid, context=None):
        if not context:
            context = {}
        previous_date_revaluation = False
        asset_id = context.get('active_id')
        revaluation_obj = self.pool.get('account.asset.revaluation')
        revaluation_ids = revaluation_obj.search(cr, uid, [('asset_id','=',asset_id)], order='id desc')
        if revaluation_ids:
            revaluation = revaluation_obj.browse(cr, uid, revaluation_ids[0])
            previous_date_revaluation = revaluation.date_revaluation
        
        return previous_date_revaluation
    
    def _get_revaluation_account(self, cr, uid, context=None):
        if not context:
            context = {}
        acc = False
        asset_obj = self.pool.get('account.asset.asset')
        asset = asset_obj.browse(cr, uid, context.get('active_id'))
        if asset:
            acc = asset.category_id.account_revaluation_value_id
        return acc and acc.id or False
    
    def _get_previous_value(self, cr, uid, context=None):
        if not context:
            context = {}
        previous_value = False
        asset_id = context.get('active_id')
        revaluation_obj = self.pool.get('account.asset.revaluation')
        asset_obj = self.pool.get('account.asset.asset')
        revaluation_ids = revaluation_obj.search(cr, uid, [('asset_id','=',asset_id)], order='id desc')
        if revaluation_ids:
            revaluation = revaluation_obj.browse(cr, uid, revaluation_ids[0])
            previous_value = revaluation.revaluated_value
        
        if not previous_value:
            asset = asset_obj.browse(cr, uid, asset_id)
            previous_value = asset.purchase_value
            
        return previous_value
    
    def _get_value_residual(self, cr, uid, context=None):
        if not context:
            context = {}
        acc = False
        asset_obj = self.pool.get('account.asset.asset')
        asset = asset_obj.browse(cr, uid, context.get('active_id'))
        if asset:
            acc = asset.value_residual
        return acc

    _columns = {
        'previous_date_revaluation': fields.date('Date', required=True),
        'date_revaluation': fields.date('Date', required=True),
        'previous_value': fields.float('Old Value', required=True),
        'previous_value_residual': fields.float('Old Value Residual', required=True),
        'revaluated_value': fields.float('New Value', required=True),
        'account_revaluation_id': fields.many2one(
            'account.account', 'Revaluation Value Account',
            domain=[('type', '<>', 'view')], required=True, store=False),
        'note': fields.text('Notes'),
    }
    
    _defaults = {
        'previous_date_revaluation': _get_previous_date_revaluation,
        'account_revaluation_id': _get_revaluation_account,
        'previous_value': _get_previous_value,
        'previous_value_residual': _get_value_residual,
    }

    def _check_revaluated_value(self, cr, uid, ids, context=None):
        for revaluation in self.browse(cr, uid, ids, context=context):
            if revaluation.revaluated_value < 0:
                return False
        return True

    _constraints = [(
        _check_revaluated_value,
        "The New Value must be positive or 0 (zero)!",
        ['revaluated_value']
    )]

    def revaluate(self, cr, uid, ids, context=None):
        asset_obj = self.pool.get('account.asset.asset')
        asset_line_obj = self.pool.get('account.asset.depreciation.line')
        move_obj = self.pool.get('account.move')
        period_obj = self.pool.get('account.period')
        revaluation_obj = self.pool.get('account.asset.revaluation')

        asset_id = context['active_id']
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        asset_ref = asset.code and '%s (ref: %s)' \
            % (asset.name, asset.code) or asset.name
        wiz_data = self.browse(cr, uid, ids[0], context=context)
        new_value = wiz_data.revaluated_value

        if context.get('early_removal'):
            residual_value, previous_id = self._prepare_last_depreciacion(
                cr, uid, asset, wiz_data.date_revaluation, context=context)
        else:
            residual_value = asset.value_residual
            
        ctx = dict(context, company_id=asset.company_id.id)
        ctx.update(account_period_prefer_normal=True)
        period_ids = period_obj.find(
            cr, uid, wiz_data.date_revaluation, context=ctx)
        period_id = period_ids[0]
        dl_ids = asset_line_obj.search(
            cr, uid,
            [('asset_id', '=', asset.id), ('type', '=', 'depreciate')],
            order='line_date desc')
        if dl_ids:
            last_date = asset_line_obj.browse(
                cr, uid, dl_ids[0], context=context).line_date
        else:
            create_dl_id = asset_line_obj.search(
                cr, uid,
                [('asset_id', '=', asset.id), ('type', '=', 'create')],
                context=context)[0]
            last_date = asset_line_obj.browse(cr, uid, create_dl_id).line_date
        if wiz_data.date_revaluation < last_date:
            raise orm.except_orm(
                _('Error!'),
                _("The revaluation date must be after "
                  "the last depreciation date."))

        line_name = asset_obj._get_revaluation_entry_name(
            cr, uid, asset, len(dl_ids) + 1, context=context)
        journal_id = asset.category_id.journal_id.id

        # create move
        move_vals = {
            'name': asset.name,
            'date': wiz_data.date_revaluation,
            'ref': line_name,
            'period_id': period_id,
            'journal_id': journal_id,
            'narration': wiz_data.note,
            }
        move_id = move_obj.create(cr, uid, move_vals, context=context)

        # create depreciation line
        asset_line_vals = {
            'amount': new_value,
            'previous_id': previous_id,
            'asset_id': asset_id,
            'name': line_name,
            'line_date': wiz_data.date_revaluation,
            'move_id': move_id,
            'type': 'revaluate',
        }
        depr_id = asset_line_obj.create(cr, uid, asset_line_vals, context=context)
        if new_value == 0:
            state = 'close'
        else:
            state = 'open'
        asset.write({'date_revaluation': wiz_data.date_revaluation,
                     'state' : state})

        # create move lines
        move_lines, balance = self._get_revaluation_data(
            cr, uid, wiz_data, asset, residual_value, wiz_data.revaluated_value, context=context)
        move_obj.write(cr, uid, [move_id], {'line_id': move_lines},
                       context=dict(context, allow_asset=True))
        
        # create revaluation line (for history)
        revaluation_line_vals = {
            'previous_date_revaluation': wiz_data.previous_date_revaluation,
            'date_revaluation': wiz_data.date_revaluation,
            'depr_id': depr_id,
            'asset_id': asset.id,
            'previous_value': wiz_data.previous_value,
            'previous_value_residual': wiz_data.previous_value_residual,
            'revaluated_value': wiz_data.revaluated_value,
            'account_revaluation_id': wiz_data.account_revaluation_id.id,
            'note':  wiz_data.note,
        }        revaluation_obj.create(cr, uid, revaluation_line_vals, context=context)
        
        asset.write({'profit_loss_disposal': balance,
                     'purchase_value' :  wiz_data.previous_value #needed to trigger recomputation
        })
        
        return {
            'name': _("Asset '%s' Revaluation Journal Entry") % asset_ref,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': context,
            'nodestroy': True,
            'domain': [('id', '=', move_id)],
        }
        
    def _prepare_last_depreciacion(self, cr, uid,
                               asset, date_revaluation, context=None):
        """
        Generate last depreciation entry on the day before the revaluation date.
        """
        asset_line_obj = self.pool.get('account.asset.depreciation.line')

        digits = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')

        dl_ids = asset_line_obj.search(
            cr, uid,
            [('asset_id', '=', asset.id), ('type', '=', 'depreciate'),
             ('init_entry', '=', False), ('move_check', '=', False)],
            order='line_date asc')
        
        if not dl_ids:
            return asset.value_residual, None
        
        first_to_depreciate_dl = asset_line_obj.browse(cr, uid, dl_ids[0])

        first_date = first_to_depreciate_dl.line_date
        if date_revaluation > first_date:
            raise orm.except_orm(
                _('Error!'),
                _("You can't make a revaluation if all the depreciation "
                  "lines for previous periods are not posted."))

        if first_to_depreciate_dl.previous_id:
            last_depr_date = first_to_depreciate_dl.previous_id.line_date
        else:
            create_dl_id = asset_line_obj.search(
                cr, uid,
                [('asset_id', '=', asset.id), ('type', '=', 'create')],
                context=context)[0]
            create_dl = asset_line_obj.browse(
                cr, uid, create_dl_id, context=context)
            last_depr_date = create_dl.line_date
        period_number_days = (
            datetime.strptime(first_date, '%Y-%m-%d') -
            datetime.strptime(last_depr_date, '%Y-%m-%d')).days
        date_revaluation = datetime.strptime(date_revaluation, '%Y-%m-%d')
        new_line_date = date_revaluation + relativedelta(days=-1)
        to_depreciate_days = (
            new_line_date -
            datetime.strptime(last_depr_date, '%Y-%m-%d')).days
        to_depreciate_amount = round(
            float(to_depreciate_days) / float(period_number_days) *
            first_to_depreciate_dl.amount, digits)
        residual_value = asset.value_residual - to_depreciate_amount
        if to_depreciate_amount:
            update_vals = {
                'amount': to_depreciate_amount,
                'line_date': new_line_date
            }
            first_to_depreciate_dl.write(update_vals)
            asset_line_obj.create_move(
                cr, uid, [dl_ids[0]], context=context)
            dl_ids.pop(0)
        asset_line_obj.unlink(cr, uid, dl_ids, context=context)
        return residual_value, first_to_depreciate_dl.id
    
    def _get_revaluation_data(self, cr, uid, wiz_data, asset, residual_value, new_value,
                          context=None):
        move_lines = []
        partner_id = asset.partner_id and asset.partner_id.id or False
        categ = asset.category_id

        depr_amount = None
        if new_value == 0.0:
            # asset and asset depreciation account reversal
            depr_amount = asset.asset_value - residual_value
            if depr_amount:
                move_line_vals = {
                    'name': asset.name,
                    'account_id': categ.account_depreciation_id.id,
                    'debit': depr_amount > 0 and depr_amount or 0.0,
                    'credit': depr_amount < 0 and -depr_amount or 0.0,
                    'partner_id': partner_id,
                    'asset_id': asset.id
                }
                move_lines.append((0, 0, move_line_vals))
                move_line_vals = {
                    'name': asset.name,
                    'account_id': categ.account_asset_id.id,
                    'debit': depr_amount < 0 and -depr_amount or 0.0,
                    'credit': depr_amount > 0 and depr_amount or 0.0,
                    'partner_id': partner_id,
                    'asset_id': asset.id
                }
                move_lines.append((0, 0, move_line_vals))
                
                #profit due to devaluation to zero (write off depreciations)
                move_line_vals = {
                    'name': asset.name,
                    'account_id': categ.account_asset_id.id,
                    'debit': depr_amount > 0 and depr_amount or 0.0,
                    'credit': depr_amount < 0 and -depr_amount or 0.0,
                    'partner_id': partner_id,
                    'asset_id': asset.id
                }
                move_lines.append((0, 0, move_line_vals))
                move_line_vals = {
                    'name': asset.name,
                    'account_id': categ.account_plus_value_id.id,
                    'debit': depr_amount < 0 and -depr_amount or 0.0,
                    'credit': depr_amount > 0 and depr_amount or 0.0,
                    'partner_id': partner_id,
                    'asset_id': asset.id
                }
                move_lines.append((0, 0, move_line_vals))
        
        # asset and asset revaluation account reversal
        move_amount = new_value - asset.asset_value
        if move_amount:
            move_line_vals = {
                'name': asset.name,
                'account_id': wiz_data.account_revaluation_id.id,
                'debit': move_amount < 0 and -move_amount or 0.0,
                'credit': move_amount > 0 and move_amount or 0.0,
                'partner_id': partner_id,
                'asset_id': asset.id
            }
            move_lines.append((0, 0, move_line_vals))
            move_line_vals = {
                'name': asset.name,
                'account_id': categ.account_asset_id.id,
                'debit': move_amount > 0 and move_amount or 0.0,
                'credit': move_amount < 0 and -move_amount or 0.0,
                'partner_id': partner_id,
                'asset_id': asset.id
            }
            move_lines.append((0, 0, move_line_vals))

        return move_lines, depr_amount

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
