# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
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

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# List of move's fields that can't be modified if move is linked
# with a depreciation line
FIELDS_AFFECTS_ASSET_MOVE = set(['journal_id', 'date'])
# List of move line's fields that can't be modified if move is linked
# with a depreciation line
FIELDS_AFFECTS_ASSET_MOVE_LINE = \
    set(['credit', 'debit', 'account_id', 'journal_id', 'date',
         'asset_profile_id', 'asset_id'])


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def unlink(self):
        for move in self:
            deprs = self.env['account.asset.line'].search(
                [('move_id', '=', move.id),
                 ('type', 'in', ['depreciate', 'remove'])])
            if deprs and not self._context.get('unlink_from_asset'):
                raise UserError(
                    _('Error!'),
                    _("You are not allowed to remove an accounting entry "
                      "linked to an asset."
                      "\nYou should remove such entries from the asset."))
        return super(AccountMove, self).unlink()

    @api.multi
    def write(self, vals):
        if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE):
            for move in self:
                deprs = self.env['account.asset.line'].search(
                    [('move_id', '=', move.id), ('type', '=', 'depreciate')])
                if deprs:
                    raise UserError(
                        _('Error!'),
                        _("You cannot change an accounting entry "
                          "linked to an asset depreciation line."))
        return super(AccountMove, self).write(vals)

    @api.multi
    def post(self):
        res = super(AccountMove, self).post()
        for rec in self:
            rec._update_assets_code()
        return res

    @api.multi
    def _update_assets_code(self):
        self.ensure_one()
        move_name = self.name
        assets = self.line_ids.mapped('asset_id')
        for index, asset in enumerate(assets):
            asset.code = move_name
            asset_line_name = asset._get_depreciation_entry_name(index)
            asset.depreciation_line_ids[0].with_context(
                {'allow_asset_line_update': True}
            ).name = asset_line_name


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    asset_profile_id = fields.Many2one(
        'account.asset.profile',
        string='Asset Category')
    asset_id = fields.Many2one(
        'account.asset', 'Asset', ondelete="restrict")

    @api.onchange('account_id')
    def _onchange_account_id(self):
        self.asset_profile_id = self.account_id.asset_profile_id

    @api.model
    def get_asset_onchange(self, vals):
        asset_obj = self.env['account.asset']
        asset_temp = asset_obj.new(vals)
        asset_temp.onchange_profile_id()
        for field in asset_temp._fields:
            if field not in vals and asset_temp[field]:
                vals[field] = asset_temp._fields[field].\
                    convert_to_write(asset_temp[field])
        return vals

    @api.model
    def _get_asset_analytic_values(self, vals, asset_vals):
        asset_vals['account_analytic_id'] =\
            vals.get('analytic_account_id', False)

    @api.model
    def create(self, vals):
        if vals.get('asset_id') and not self._context.get('allow_asset'):
            raise UserError(
                _('Error!'),
                _("You are not allowed to link "
                  "an accounting entry to an asset."
                  "\nYou should generate such entries from the asset."))
        if vals.get('asset_profile_id'):
            # create asset
            asset_obj = self.env['account.asset']
            move = self.env['account.move'].browse(vals['move_id'])
            depreciation_base = vals['debit'] or -vals['credit']
            temp_asset = asset_obj.new({
                'name': vals['name'],
                'profile_id': vals['asset_profile_id'],
                'purchase_value': depreciation_base,
                'partner_id': vals['partner_id'],
                'date_start': move.date,
            })
            temp_asset.onchange_profile_id()
            asset_vals = temp_asset._convert_to_write(temp_asset._cache)
            self._get_asset_analytic_values(vals, asset_vals)
            if self._context.get('company_id'):
                asset_vals['company_id'] = self._context['company_id']
            ctx = dict(self._context, create_asset_from_move_line=True,
                       move_id=vals['move_id'])
            asset = asset_obj.with_context(
                ctx).create(asset_vals)
            vals['asset_id'] = asset.id
        return super(AccountMoveLine, self).create(vals)

    @api.multi
    def write(self, vals):
        for aml in self:
            if aml.asset_id:
                if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE_LINE):
                    if not self.env.context.get('allow_asset_removal') \
                            and vals.keys() == ['asset_id']:
                        raise UserError(
                            _('Error!'),
                            _("You cannot change an accounting item "
                              "linked to an asset depreciation line."))
        if vals.get('asset_id'):
            raise UserError(
                _('Error!'),
                _("You are not allowed to link "
                  "an accounting entry to an asset."
                  "\nYou should generate such entries from the asset."))
        if vals.get('asset_profile_id'):
            assert len(self.ids) == 1, \
                'This option should only be used for a single id at a time.'
            asset_obj = self.env['account.asset']
            for aml in self:
                if vals['asset_profile_id'] == aml.asset_profile_id.id:
                    continue
                # create asset
                debit = 'debit' in vals and vals.get('debit', 0.0) or aml.debit
                credit = 'credit' in vals and \
                    vals.get('credit', 0.0) or aml.credit
                asset_value = debit - credit
                partner_id = 'partner' in vals and \
                    vals.get('partner', False) or aml.partner_id.id
                date_start = 'date' in vals and \
                    vals.get('date', False) or aml.date
                asset_vals = {
                    'name': vals.get('name') or aml.name,
                    'category_id': vals['asset_category_id'],
                    'purchase_value': asset_value,
                    'partner_id': partner_id,
                    'date_start': date_start,
                    'company_id': vals.get('company_id') or aml.company_id.id,
                }
                asset_vals = asset_obj.play_onchanges(
                    asset_vals, ['profile_id'])
                ctx = dict(self._context, create_asset_from_move_line=True,
                           move_id=aml.move_id.id)
                asset = asset_obj.with_context(ctx).create(asset_vals)
                vals['asset_id'] = asset.id
        return super(AccountMoveLine, self).write(vals)
