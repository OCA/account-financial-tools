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

from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import api, fields, models, exceptions, _
import logging
_logger = logging.getLogger(__name__)


class AccountAssetRemove(models.TransientModel):
    _name = 'account.asset.remove'
    _description = 'Remove Asset'

    _residual_value_regime_countries = ['FR']

    @api.model
    def _posting_regime(self):
        return[
            ('residual_value', _('Residual Value')),
            ('gain_loss_on_sale', _('Gain/Loss on Sale')),
        ]

    @api.model
    def _get_posting_regime(self):
        asset_obj = self.env['account.asset']
        asset = asset_obj.browse(self.env.context.get('active_id'))
        country = asset and asset.company_id.country_id.code or False
        if country in self._residual_value_regime_countries:
            return 'residual_value'
        else:
            return 'gain_loss_on_sale'

    @api.model
    def _get_sale(self):
        inv_line_obj = self.env['account.invoice.line']
        asset_id = self.env.context.get('active_id')
        sale_value = 0.0
        account_sale_id = False
        inv_lines = inv_line_obj.search(
            [('asset_id', '=', asset_id)])
        for line in inv_lines:
            inv = line.invoice_id
            comp_curr = inv.company_id.currency_id
            inv_curr = inv.currency_id
            if line.invoice_id.state in ['open', 'paid']:
                account_sale_id = line.account_id.id
                amount = line.price_subtotal
                if inv_curr != comp_curr:
                    amount = comp_curr.compute(amount)
                sale_value += amount
        return {'sale_value': sale_value, 'account_sale_id': account_sale_id}

    @api.model
    def _get_sale_value(self):
        return self._get_sale()['sale_value']

    @api.model
    def _get_sale_account(self):
        return self._get_sale()['account_sale_id']

    @api.model
    def _get_plus_account(self):
        acc = self.env['account.account'].browse(False)
        asset_obj = self.env['account.asset']
        asset = asset_obj.browse(self.env.context.get('active_id'))
        if asset:
            acc = asset.profile_id.account_plus_value_id
        return acc

    @api.model
    def _get_min_account(self):
        acc = self.env['account.account'].browse(False)
        asset_obj = self.env['account.asset']
        asset = asset_obj.browse(self.env.context.get('active_id'))
        if asset:
            acc = asset.profile_id.account_min_value_id
        return acc

    @api.model
    def _get_residual_account(self):
        acc = self.env['account.account'].browse(False)
        asset_obj = self.env['account.asset']
        asset = asset_obj.browse(self.env.context.get('active_id'))
        if asset:
            acc = asset.profile_id.account_residual_value_id
        return acc

    date_remove = fields.Date(
        'Asset Removal Date', required=True,
        default=fields.Date.today,
        help="Removal date must be after the last posted entry "
             "in case of early removal")
    sale_value = fields.Float(
        'Sale Value',
        default=lambda self: self._get_sale_value())
    account_sale_id = fields.Many2one(
        'account.account', 'Asset Sale Account',
        default=lambda self: self._get_sale_account())
    account_plus_value_id = fields.Many2one(
        'account.account', 'Plus-Value Account',
        default=lambda self: self._get_plus_account())
    account_min_value_id = fields.Many2one(
        'account.account', 'Min-Value Account',
        default=lambda self: self._get_min_account())
    account_residual_value_id = fields.Many2one(
        'account.account', 'Residual Value Account',
        default=lambda self: self._get_residual_account())
    posting_regime = fields.Selection(
        selection=lambda self: self._posting_regime(),
        string='Removal Entry Policy',
        required=True,
        default=lambda self: self._get_posting_regime(),
        help="Removal Entry Policy \n"
             "  * Residual Value: The non-depreciated value will be "
             "posted on the 'Residual Value Account' \n"
             "  * Gain/Loss on Sale: The Gain or Loss will be posted on "
             "the 'Plus-Value Account' or 'Min-Value Account' ")
    note = fields.Text('Notes')

    _sql_constraints = [(
        'sale_value', 'CHECK (sale_value>=0)',
        'The Sale Value must be positive!')]

    @api.multi
    def _prepare_early_removal(self, asset):
        """
        Generate last depreciation entry on the day before the removal date.
        """
        self.ensure_one()
        date_remove = self.date_remove
        asset_line_obj = self.env['account.asset.line']

        digits = self.env['decimal.precision'].precision_get('Account')

        dlines = asset_line_obj.search(
            [('asset_id', '=', asset.id), ('type', '=', 'depreciate'),
             ('init_entry', '=', False), ('move_check', '=', False)],
            order='line_date asc')
        first_to_depreciate_dl = dlines[0]

        first_date = first_to_depreciate_dl.line_date
        if date_remove > first_date:
            raise exceptions.UserError(
                _("You can't make an early removal if all the depreciation "
                  "lines for previous periods are not posted."))

        if first_to_depreciate_dl.previous_id:
            last_depr_date = first_to_depreciate_dl.previous_id.line_date
        else:
            create_dl = asset_line_obj.search(
                [('asset_id', '=', asset.id), ('type', '=', 'create')])[0]
            last_depr_date = create_dl.line_date

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
            dlines[0].create_move()
            dlines -= dlines[0]
        dlines.unlink()
        return residual_value

    @api.multi
    def _get_removal_data(self, asset, residual_value):
        self.ensure_one()
        move_lines = []
        partner_id = asset.partner_id and asset.partner_id.id or False
        profile = asset.profile_id

        # asset and asset depreciation account reversal
        depr_amount = asset.depreciation_base - residual_value
        if depr_amount:
            move_line_vals = {
                'name': asset.name,
                'account_id': profile.account_depreciation_id.id,
                'debit': depr_amount > 0 and depr_amount or 0.0,
                'credit': depr_amount < 0 and -depr_amount or 0.0,
                'partner_id': partner_id,
                'asset_id': asset.id
            }
            move_lines.append((0, 0, move_line_vals))

        move_line_vals = {
            'name': asset.name,
            'account_id': profile.account_asset_id.id,
            'debit': (asset.depreciation_base < 0 and -asset
                      .depreciation_base or 0.0),
            'credit': (asset.depreciation_base > 0 and asset
                       .depreciation_base or 0.0),
            'partner_id': partner_id,
            'asset_id': asset.id
        }
        move_lines.append((0, 0, move_line_vals))

        if residual_value:
            if self.posting_regime == 'residual_value':
                move_line_vals = {
                    'name': asset.name,
                    'account_id': self.account_residual_value_id.id,
                    'analytic_account_id': asset.account_analytic_id.id,
                    'debit': residual_value,
                    'credit': 0.0,
                    'partner_id': partner_id,
                    'asset_id': asset.id
                }
                move_lines.append((0, 0, move_line_vals))
            elif self.posting_regime == 'gain_loss_on_sale':
                if self.sale_value:
                    sale_value = self.sale_value
                    move_line_vals = {
                        'name': asset.name,
                        'account_id': self.account_sale_id.id,
                        'analytic_account_id': asset.account_analytic_id.id,
                        'debit': sale_value,
                        'credit': 0.0,
                        'partner_id': partner_id,
                        'asset_id': asset.id
                    }
                    move_lines.append((0, 0, move_line_vals))
                balance = self.sale_value - residual_value
                account_id = (self.account_plus_value_id.id
                              if balance > 0
                              else self.account_min_value_id.id)
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

    @api.multi
    def remove(self):
        self.ensure_one()
        asset_obj = self.env['account.asset']
        asset_line_obj = self.env['account.asset.line']
        move_obj = self.env['account.move']

        asset_id = self.env.context.get('active_id')
        asset = asset_obj.browse(asset_id)
        asset_ref = asset.code and '%s (ref: %s)' \
            % (asset.name, asset.code) or asset.name

        if self.env.context.get('early_removal'):
            residual_value = self._prepare_early_removal(asset)
        else:
            residual_value = asset.value_residual

        dlines = asset_line_obj.search(
            [('asset_id', '=', asset.id), ('type', '=', 'depreciate')],
            order='line_date desc')
        if dlines:
            last_date = dlines[0].line_date
        else:
            create_dl = asset_line_obj.search(
                [('asset_id', '=', asset.id), ('type', '=', 'create')])[0]
            last_date = create_dl.line_date

        if self.date_remove < last_date:
            raise exceptions.UserError(
                _("The removal date must be after "
                  "the last depreciation date."))

        line_name = asset._get_depreciation_entry_name(len(dlines) + 1)
        journal_id = asset.profile_id.journal_id.id

        # create move
        move_vals = {
            'name': asset.name,
            'date': self.date_remove,
            'ref': line_name,
            'journal_id': journal_id,
            'narration': self.note,
            }
        move = move_obj.create(move_vals)

        # create asset line
        asset_line_vals = {
            'amount': residual_value,
            'asset_id': asset_id,
            'name': line_name,
            'line_date': self.date_remove,
            'move_id': move.id,
            'type': 'remove',
        }
        asset_line_obj.create(asset_line_vals)
        asset.write({'state': 'removed', 'date_remove': self.date_remove})

        # create move lines
        move_lines = self._get_removal_data(asset, residual_value)
        move.with_context(allow_asset=True).write({'line_ids': move_lines})

        return {
            'name': _("Asset '%s' Removal Journal Entry") % asset_ref,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'nodestroy': True,
            'domain': [('id', '=', move.id)],
        }
