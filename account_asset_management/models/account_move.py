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

from openerp import api, fields, models, _
from openerp.exceptions import UserError

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
    def create(self, vals, apply_taxes=True):
        if vals.get('asset_id') and not self._context.get('allow_asset'):
            raise UserError(
                _('Error!'),
                _("You are not allowed to link "
                  "an accounting entry to an asset."
                  "\nYou should generate such entries from the asset."))
        if vals.get('asset_profile_id'):
            # create asset
            move = self.env['account.move'].browse(vals['move_id'])
            depreciation_base = vals['debit'] or -vals['credit']
            asset_vals = {
                'name': vals['name'],
                'profile_id': vals['asset_profile_id'],
                'purchase_value': depreciation_base,
                'partner_id': vals['partner_id'],
                'date_start': move.date,
            }
            if self._context.get('company_id'):
                asset_vals['company_id'] = self._context['company_id']
            ctx = dict(self._context, create_asset_from_move_line=True,
                       move_id=vals['move_id'])
            asset = self.env['account.asset'].with_context(
                ctx).create(asset_vals)
            vals['asset_id'] = asset.id
        return super(AccountMoveLine, self).create(
            vals, apply_taxes=apply_taxes)

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
                ctx = dict(self._context, create_asset_from_move_line=True,
                           move_id=aml.move_id.id)
                asset = self.env['account.asset'].with_context(
                    ctx).create(asset_vals)
                vals['asset_id'] = asset.id
        return super(AccountMoveLine, self).write(vals)
