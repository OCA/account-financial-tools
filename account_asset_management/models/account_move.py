# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
    def unlink(self, **kwargs):
        for move in self:
            deprs = self.env['account.asset.line'].search(
                [('move_id', '=', move.id),
                 ('type', 'in', ['depreciate', 'remove'])])
            if deprs and not self._context.get('unlink_from_asset'):
                raise UserError(
                    _("You are not allowed to remove an accounting entry "
                      "linked to an asset."
                      "\nYou should remove such entries from the asset."))
            # trigger store function
            deprs.write({'move_id': False})
        return super(AccountMove, self).unlink(**kwargs)

    @api.multi
    def write(self, vals):
        if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE):
            for move in self:
                deprs = self.env['account.asset.line'].search(
                    [('move_id', '=', move.id), ('type', '=', 'depreciate')])
                if deprs:
                    raise UserError(
                        _("You cannot change an accounting entry "
                          "linked to an asset depreciation line."))
        return super(AccountMove, self).write(vals)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    asset_profile_id = fields.Many2one(
        comodel_name='account.asset.profile',
        string='Asset Profile')
    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset', ondelete='restrict')

    @api.onchange('account_id')
    def _onchange_account_id(self):
        self.asset_profile_id = self.account_id.asset_profile_id

    @api.model
    def create(self, vals, **kwargs):
        if vals.get('asset_id') and not self._context.get('allow_asset'):
            raise UserError(
                _("You are not allowed to link "
                  "an accounting entry to an asset."
                  "\nYou should generate such entries from the asset."))
        if vals.get('asset_profile_id'):
            # create asset
            asset_obj = self.env['account.asset']
            move = self.env['account.move'].browse(vals['move_id'])
            depreciation_base = vals['debit'] or -vals['credit']
            temp_vals = {
                'name': vals['name'],
                'profile_id': vals['asset_profile_id'],
                'purchase_value': depreciation_base,
                'partner_id': vals['partner_id'],
                'date_start': move.date,
            }
            if self._context.get('company_id'):
                temp_vals['company_id'] = self._context['company_id']
            temp_asset = asset_obj.new(temp_vals)
            temp_asset._onchange_profile_id()
            asset_vals = temp_asset._convert_to_write(temp_asset._cache)
            self._get_asset_analytic_values(vals, asset_vals)
            ctx = dict(self._context, create_asset_from_move_line=True,
                       move_id=vals['move_id'])
            asset = asset_obj.with_context(
                ctx).create(asset_vals)
            vals['asset_id'] = asset.id
        return super(AccountMoveLine, self).create(vals, **kwargs)

    @api.multi
    def write(self, vals, **kwargs):
        for aml in self:
            if aml.asset_id:
                if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE_LINE):
                    if not (self.env.context.get('allow_asset_removal') and
                            vals.keys() == ['asset_id']):
                        raise UserError(
                            _("You cannot change an accounting item "
                              "linked to an asset depreciation line."))
        if vals.get('asset_id'):
            raise UserError(
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
                depreciation_base = debit - credit
                partner_id = 'partner' in vals and \
                    vals.get('partner', False) or aml.partner_id.id
                date_start = 'date' in vals and \
                    vals.get('date', False) or aml.date
                asset_vals = {
                    'name': vals.get('name') or aml.name,
                    'profile_id': vals['asset_profile_id'],
                    'purchase_value': depreciation_base,
                    'partner_id': partner_id,
                    'date_start': date_start,
                    'company_id': vals.get('company_id') or aml.company_id.id,
                }
                self._play_onchange_profile_id(asset_vals)
                self._get_asset_analytic_values(vals, asset_vals)
                ctx = dict(self._context, create_asset_from_move_line=True,
                           move_id=aml.move_id.id)
                asset = asset_obj.with_context(ctx).create(asset_vals)
                vals['asset_id'] = asset.id
        return super(AccountMoveLine, self).write(vals, **kwargs)

    @api.model
    def _get_asset_analytic_values(self, vals, asset_vals):
        asset_vals['account_analytic_id'] = \
            vals.get('analytic_account_id', False)

    @api.model
    def _play_onchange_profile_id(self, vals):
        asset_obj = self.env['account.asset']
        asset_temp = asset_obj.new(vals)
        asset_temp._onchange_profile_id()
        for field in asset_temp._fields:
            if field not in vals and asset_temp[field]:
                vals[field] = asset_temp._fields[field].\
                    convert_to_write(asset_temp[field], asset_temp)
