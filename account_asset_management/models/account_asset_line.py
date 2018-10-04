# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
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

import time
from odoo import api, fields, exceptions, models, _
import odoo.addons.decimal_precision as dp


class AccountAssetLine(models.Model):
    _name = 'account.asset.line'
    _description = 'Asset depreciation line'
    _order = 'type, line_date'

    @api.depends('amount', 'asset_id.depreciation_line_ids')
    @api.multi
    def _compute(self):
        # When modifying amount or adding a depreciation line to an asset,
        # recompute all lines of the asset to ensure coherent values.
        # TODO: not sure that remaining_value and depreciated_value should be
        # computed fields
        assets = self.mapped('asset_id')

        for asset in assets:
            # Always recompute all lines of an asset
            depreciation_base = asset.depreciation_base
            lines = self.search([
                ('asset_id', '=', asset.id),
                ('type', '=', 'depreciate'),
            ], order='line_date')

            depreciated_value = 0.0
            remaining_value = 0.0

            for dl in lines:
                if not dl.previous_id:
                    depreciated_value = 0.0
                    remaining_value = (
                        depreciation_base - depreciated_value - dl.amount)
                else:
                    depreciated_value += dl.previous_id.amount
                    remaining_value -= dl.amount
                dl.depreciated_value = depreciated_value
                dl.remaining_value = remaining_value

    @api.depends('move_id')
    @api.multi
    def _move_check(self):
        for line in self:
            line.move_check = bool(line.move_id)

    name = fields.Char('Depreciation Name', size=64, readonly=True)
    asset_id = fields.Many2one(
        'account.asset', 'Asset',
        required=True, ondelete='cascade')
    previous_id = fields.Many2one(
        'account.asset.line', 'Previous Depreciation Line',
        readonly=True)
    parent_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('open', 'Running'),
            ('close', 'Close'),
            ('removed', 'Removed'),
        ],
        related='asset_id.state', string='State of Asset')
    depreciation_base = fields.Float(
        related='asset_id.depreciation_base', string='Asset Value')
    amount = fields.Float(
        'Amount', digits=dp.get_precision('Account'),
        required=True)
    remaining_value = fields.Float(
        compute='_compute',
        digits=dp.get_precision('Account'),
        string='Next Period Depreciation',
        store=True)
    depreciated_value = fields.Float(
        compute='_compute',
        digits=dp.get_precision('Account'),
        string='Amount Already Depreciated',
        store=True)
    line_date = fields.Date('Date', required=True)
    move_id = fields.Many2one(
        'account.move', 'Depreciation Entry', readonly=True)
    move_check = fields.Boolean(
        compute='_move_check',
        string='Posted',
        store=True)
    type = fields.Selection([
        ('create', 'Asset Value'),
        ('depreciate', 'Depreciation'),
        ('remove', 'Asset Removal'),
        ], 'Type', readonly=True, default='depreciate')
    init_entry = fields.Boolean(
        'Initial Balance Entry',
        help="Set this flag for entries of previous fiscal years "
             "for which OpenERP has not generated accounting entries.")

    @api.onchange('type', 'depreciation_base', 'amount', 'depreciated_value')
    def onchange_amount(self):
        if self.type == 'depreciate':
            self.remaining_value = self.depreciation_base - \
                self.depreciated_value - self.amount

    @api.multi
    def unlink(self):
        for dl in self:
            if dl.type == 'create':
                raise exceptions.UserError(
                    _("You cannot remove an asset line "
                      "of type 'Asset Value'."))
            elif dl.move_id:
                raise exceptions.UserError(
                    _("You cannot delete a depreciation line with "
                      "an associated accounting entry."))
            previous_id = dl.previous_id.id or False
            self.env.cr.execute(
                "SELECT id FROM account_asset_line "
                "WHERE previous_id = %s" % dl.id)
            next = self.env.cr.fetchone()
            if next:
                next_id = next[0]
                self.browse(next_id).write({'previous_id': previous_id})
        return super(AccountAssetLine, self).unlink()

    @api.multi
    def write(self, vals):
        for dl in self:
            if vals.keys() == ['move_id'] and not vals['move_id']:
                # allow to remove an accounting entry via the
                # 'Delete Move' button on the depreciation lines.
                if not self.env.context.get('unlink_from_asset'):
                    raise exceptions.UserError(
                        _("You are not allowed to remove an accounting entry "
                          "linked to an asset."
                          "\nYou should remove such entries from the asset."))
            elif vals.keys() == ['asset_id']:
                continue
            elif dl.move_id and not self.env.context.get(
                    'allow_asset_line_update'):
                raise exceptions.UserError(
                    _("You cannot change a depreciation line "
                      "with an associated accounting entry."))
            elif vals.get('init_entry'):
                self.env.cr.execute(
                    "SELECT id "
                    "FROM account_asset_line "
                    "WHERE asset_id = %s AND move_check = TRUE "
                    "AND type = 'depreciate' AND line_date <= %s LIMIT 1",
                    (dl.asset_id.id, dl.line_date))
                res = self.env.cr.fetchone()
                if res:
                    raise exceptions.UserError(
                        _("You cannot set the 'Initial Balance Entry' flag "
                          "on a depreciation line "
                          "with prior posted entries."))
            elif vals.get('line_date'):
                self.env.cr.execute(
                    "SELECT id "
                    "FROM account_asset_line "
                    "WHERE asset_id = %s "
                    "AND (init_entry=TRUE OR move_check=TRUE)"
                    "AND line_date > %s LIMIT 1",
                    (dl.asset_id.id, vals['line_date']))
                res = self.env.cr.fetchone()
                if res:
                    raise exceptions.UserError(
                        _("You cannot set the date on a depreciation line "
                          "prior to already posted entries."))
        return super(AccountAssetLine, self).write(vals)

    @api.multi
    def _setup_move_data(self, depreciation_date):
        self.ensure_one()
        asset = self.asset_id
        move_data = {
            'name': asset.name,
            'date': depreciation_date,
            'ref': self.name,
            'journal_id': asset.profile_id.journal_id.id,
        }
        return move_data

    @api.multi
    def _setup_move_line_data(self, depreciation_date, account_id, type,
                              move_id):
        self.ensure_one()
        asset = self.asset_id
        amount = self.amount
        analytic_id = False
        if type == 'depreciation':
            debit = amount < 0 and -amount or 0.0
            credit = amount > 0 and amount or 0.0
        elif type == 'expense':
            debit = amount > 0 and amount or 0.0
            credit = amount < 0 and -amount or 0.0
            analytic_id = asset.account_analytic_id.id
        move_line_data = {
            'name': asset.name,
            'ref': self.name,
            'move_id': move_id,
            'account_id': account_id,
            'credit': credit,
            'debit': debit,
            'journal_id': asset.profile_id.journal_id.id,
            'partner_id': asset.partner_id.id,
            'analytic_account_id': analytic_id,
            'date': depreciation_date,
            'asset_id': asset.id,
        }
        return move_line_data

    @api.multi
    def create_move(self):
        asset_obj = self.env['account.asset']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        created_move_ids = []
        asset_ids = []
        for line in self:
            asset = line.asset_id
            if asset.method_time == 'year':
                depreciation_date = self.env.context.get(
                    'depreciation_date') or line.line_date
            else:
                depreciation_date = self.env.context.get(
                    'depreciation_date') or time.strftime('%Y-%m-%d')
            move = move_obj.create(line._setup_move_data(
                depreciation_date))
            depr_acc_id = asset.profile_id.account_depreciation_id.id
            exp_acc_id = asset.profile_id.account_expense_depreciation_id.id
            move_line_obj = move_line_obj.with_context(allow_asset=True)
            move_line_obj.with_context(check_move_validity=False).create(
                line._setup_move_line_data(depreciation_date, depr_acc_id,
                                           'depreciation', move.id))
            move_line_obj.create(line._setup_move_line_data(
                depreciation_date, exp_acc_id, 'expense', move.id))
            line.with_context(allow_asset_line_update=True).write(
                {'move_id': move.id})
            created_move_ids.append(move.id)
            asset_ids.append(asset.id)
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(list(set(asset_ids))):
            if asset.company_id.currency_id.is_zero(asset.value_residual):
                asset.write({'state': 'close'})
        return created_move_ids

    @api.multi
    def open_move(self):
        self.ensure_one()
        return {
            'name': _("Journal Entry"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'nodestroy': True,
            'domain': [('id', '=', self.move_id.id)],
        }

    @api.multi
    def unlink_move(self):
        for line in self:
            move = line.move_id
            if move.state == 'posted':
                move.button_cancel()
            move.with_context(unlink_from_asset=True).unlink()
            # trigger store function
            line.with_context(unlink_from_asset=True).write({'move_id': False})
            if line.parent_state == 'close':
                line.asset_id.write({'state': 'open'})
            elif line.parent_state == 'removed' and line.type == 'remove':
                line.asset_id.write({'state': 'close'})
                line.unlink()
        return True
