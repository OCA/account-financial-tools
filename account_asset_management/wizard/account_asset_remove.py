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
from dateutil.relativedelta import relativedelta
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class account_asset_remove(orm.TransientModel):
    _name = 'account.asset.remove'
    _description = 'Remove Asset'

    _residual_value_regime_countries = ['FR']

    def _posting_regime(self, cr, uid, context=None):
        return[
            ('residual_value', _('Residual Value')),
            ('gain_loss_on_sale', _('Gain/Loss on Sale')),
        ]

    def _get_posting_regime(self, cr, uid, context=None):
        if not context:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        asset = asset_obj.browse(cr, uid, context.get('active_id'))
        country = asset and asset.company_id.country_id.code or False
        if country in self._residual_value_regime_countries:
            return 'residual_value'
        else:
            return 'gain_loss_on_sale'

    def _get_sale(self, cr, uid, context=None):
        if not context:
            context = {}
        inv_line_obj = self.pool.get('account.invoice.line')
        currency_obj = self.pool.get('res.currency')
        asset_id = context.get('active_id')
        sale_value = 0.0
        account_sale_id = False
        inv_line_ids = inv_line_obj.search(
            cr, uid, [('asset_id', '=', asset_id)], context=context)
        for line in inv_line_obj.browse(cr, uid, inv_line_ids):
            inv = line.invoice_id
            comp_curr = inv.company_id.currency_id
            inv_curr = inv.currency_id
            if line.invoice_id.state in ['open', 'paid']:
                account_sale_id = line.account_id.id
                amount = line.price_subtotal
                if inv_curr != comp_curr:
                    amount = currency_obj.compute(
                        cr, uid, inv_curr.id, comp_curr.id, amount,
                        context=context)
                sale_value += amount
        return {'sale_value': sale_value, 'account_sale_id': account_sale_id}

    def _get_sale_value(self, cr, uid, context=None):
        return self._get_sale(cr, uid, context=context)['sale_value']

    def _get_sale_account(self, cr, uid, context=None):
        return self._get_sale(cr, uid, context=context)['account_sale_id']

    def _get_plus_account(self, cr, uid, context=None):
        if not context:
            context = {}
        acc = False
        asset_obj = self.pool.get('account.asset.asset')
        asset = asset_obj.browse(cr, uid, context.get('active_id'))
        if asset:
            acc = asset.category_id.account_plus_value_id
        return acc and acc.id or False

    def _get_min_account(self, cr, uid, context=None):
        if not context:
            context = {}
        acc = False
        asset_obj = self.pool.get('account.asset.asset')
        asset = asset_obj.browse(cr, uid, context.get('active_id'))
        if asset:
            acc = asset.category_id.account_min_value_id
        return acc and acc.id or False

    def _get_residual_account(self, cr, uid, context=None):
        if not context:
            context = {}
        acc = False
        asset_obj = self.pool.get('account.asset.asset')
        asset = asset_obj.browse(cr, uid, context.get('active_id'))
        if asset:
            acc = asset.category_id.account_residual_value_id
        return acc and acc.id or False

    _columns = {
        'date_remove': fields.date(
            'Asset Removal Date', required=True,
            help="Removal date must be after the last posted entry "
                 "in case of early removal"),
        'period_id': fields.many2one(
            'account.period', 'Force Period',
            domain=[('state', '<>', 'done')],
            help="Keep empty to use the period of the removal ate."),
        'sale_value': fields.float('Sale Value'),
        'account_sale_id': fields.many2one(
            'account.account', 'Asset Sale Account',
            domain=[('type', '=', 'other')]),
        'account_plus_value_id': fields.many2one(
            'account.account', 'Plus-Value Account',
            domain=[('type', '=', 'other')]),
        'account_min_value_id': fields.many2one(
            'account.account', 'Min-Value Account',
            domain=[('type', '=', 'other')]),
        'account_residual_value_id': fields.many2one(
            'account.account', 'Residual Value Account',
            domain=[('type', '=', 'other')]),
        'posting_regime': fields.selection(
            _posting_regime, 'Removal Entry Policy',
            required=True,
            help="Removal Entry Policy \n"
                 "  * Residual Value: The non-depreciated value will be "
                 "posted on the 'Residual Value Account' \n"
                 "  * Gain/Loss on Sale: The Gain or Loss will be posted on "
                 "the 'Plus-Value Account' or 'Min-Value Account' "),
        'note': fields.text('Notes'),
    }

    _defaults = {
        'sale_value': _get_sale_value,
        'account_sale_id': _get_sale_account,
        'account_plus_value_id': _get_plus_account,
        'account_min_value_id': _get_min_account,
        'account_residual_value_id': _get_residual_account,
        'posting_regime': _get_posting_regime,
    }

    _sql_constraints = [(
        'sale_value', 'CHECK (sale_value>=0)',
        'The Sale Value must be positive!')]

    def _prepare_early_removal(self, cr, uid,
                               asset, date_remove, context=None):
        """
        Generate last depreciation entry on the day before the removal date.
        """
        asset_line_obj = self.pool.get('account.asset.depreciation.line')

        digits = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')

        dl_ids = asset_line_obj.search(
            cr, uid,
            [('asset_id', '=', asset.id), ('type', '=', 'depreciate'),
             ('init_entry', '=', False), ('move_check', '=', False)],
            order='line_date asc')
        first_to_depreciate_dl = asset_line_obj.browse(cr, uid, dl_ids[0])

        first_date = first_to_depreciate_dl.line_date
        if date_remove > first_date:
            raise orm.except_orm(
                _('Error!'),
                _("You can't make an early removal if all the depreciation "
                  "lines for previous periods are not posted."))

        last_depr_date = first_to_depreciate_dl.previous_id.line_date
        period_number_days = (
            datetime.strptime(first_date, '%Y-%m-%d') -
            datetime.strptime(last_depr_date, '%Y-%m-%d')).days
        date_remove = datetime.strptime(date_remove, '%Y-%m-%d')
        new_line_date = date_remove + relativedelta(days=-1)
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
        return residual_value

    def _get_removal_data(self, cr, uid, wiz_data, asset, residual_value,
                          context=None):
        move_lines = []
        partner_id = asset.partner_id and asset.partner_id.id or False
        categ = asset.category_id

        # asset and asset depreciation account reversal
        depr_amount = asset.asset_value - residual_value
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
            'debit': asset.asset_value < 0 and -asset.asset_value or 0.0,
            'credit': asset.asset_value > 0 and asset.asset_value or 0.0,
            'partner_id': partner_id,
            'asset_id': asset.id
        }
        move_lines.append((0, 0, move_line_vals))

        if residual_value:
            if wiz_data.posting_regime == 'residual_value':
                move_line_vals = {
                    'name': asset.name,
                    'account_id': wiz_data.account_residual_value_id.id,
                    'analytic_account_id': asset.account_analytic_id.id,
                    'debit': residual_value,
                    'credit': 0.0,
                    'partner_id': partner_id,
                    'asset_id': asset.id
                }
                move_lines.append((0, 0, move_line_vals))
            elif wiz_data.posting_regime == 'gain_loss_on_sale':
                if wiz_data.sale_value:
                    sale_value = wiz_data.sale_value
                    move_line_vals = {
                        'name': asset.name,
                        'account_id': wiz_data.account_sale_id.id,
                        'analytic_account_id': asset.account_analytic_id.id,
                        'debit': sale_value,
                        'credit': 0.0,
                        'partner_id': partner_id,
                        'asset_id': asset.id
                    }
                    move_lines.append((0, 0, move_line_vals))
                balance = wiz_data.sale_value - residual_value
                account_id = (wiz_data.account_plus_value_id.id
                              if balance > 0
                              else wiz_data.account_min_value_id.id)
                move_line_vals = {
                    'name': asset.name,
                    'account_id': account_id,
                    'analytic_account_id': asset.account_analytic_id.id,
                    'debit': balance < 0 and -balance or 0.0,
                    'credit': balance > 0 and balance or 0.0,
                    'partner_id': partner_id,
                    'asset_id': asset.id
                }
                move_lines.append((0, 0, move_line_vals))

        return move_lines

    def remove(self, cr, uid, ids, context=None):
        asset_obj = self.pool.get('account.asset.asset')
        asset_line_obj = self.pool.get('account.asset.depreciation.line')
        move_obj = self.pool.get('account.move')
        period_obj = self.pool.get('account.period')

        asset_id = context['active_id']
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        asset_ref = asset.code and '%s (ref: %s)' \
            % (asset.name, asset.code) or asset.name
        wiz_data = self.browse(cr, uid, ids[0], context=context)

        if context.get('early_removal'):
            residual_value = self._prepare_early_removal(
                cr, uid, asset, wiz_data.date_remove, context=context)
        else:
            residual_value = asset.value_residual

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

        # create asset line
        asset_line_vals = {
            'amount': residual_value,
            'asset_id': asset_id,
            'name': line_name,
            'line_date': wiz_data.date_remove,
            'move_id': move_id,
            'type': 'remove',
        }
        asset_line_obj.create(cr, uid, asset_line_vals, context=context)
        asset.write({'state': 'removed', 'date_remove': wiz_data.date_remove})

        # create move lines
        move_lines = self._get_removal_data(
            cr, uid, wiz_data, asset, residual_value, context=context)
        move_obj.write(cr, uid, [move_id], {'line_id': move_lines},
                       context=dict(context, allow_asset=True))

        return {
            'name': _("Asset '%s' Removal Journal Entry") % asset_ref,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': context,
            'nodestroy': True,
            'domain': [('id', '=', move_id)],
        }
