# -*- coding: utf-8 -*-
# Copyright 2010-2012 OpenERP s.a. (<http://openerp.com>)
# Copyright 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

# List of move's fields that can't be modified if move is linked
# with a depreciation line
FIELDS_AFFECTS_ASSET_MOVE = set(['period_id', 'journal_id', 'date'])
# List of move line's fields that can't be modified if move is linked
# with a depreciation line
FIELDS_AFFECTS_ASSET_MOVE_LINE = \
    set(['credit', 'debit', 'account_id', 'journal_id', 'date',
         'asset_category_id', 'asset_id', 'tax_code_id', 'tax_amount'])


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def unlink(self, check=True):
        depr_obj = self.env['account.asset.depreciation.line']
        for move_id in self:
            depr_ids = depr_obj.search(
                [('move_id', '=', move_id.id),
                 ('type', 'in', ['depreciate', 'remove'])])
            if depr_ids and not self.env.context.get('unlink_from_asset'):
                raise ValidationError(
                    _("You are not allowed to remove an accounting entry "
                      "linked to an asset."
                      "\nYou should remove such entries from the asset."))
            # trigger store function
            depr_ids.write({'move_id': False})
        return super(AccountMove, self).unlink(check=check)

    @api.multi
    def write(self, vals):
        if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE):
            depr_obj = self.env['account.asset.depreciation.line']
            for move_id in self:
                depr_ids = depr_obj.search_count([
                    ('move_id', '=', move_id.id),
                    ('type', '=', 'depreciate')])
                if depr_ids:
                    raise ValidationError(
                        _("You cannot change an accounting entry "
                          "linked to an asset depreciation line."))
        return super(AccountMove, self).write(vals)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    asset_category_id = fields.Many2one(
        'account.asset.category',
        'Asset Category',
    )
    asset_id = fields.Many2one(
        'account.asset.asset',
        'Asset',
        ondelete="restrict",
    )

    @api.onchange('account_id')
    def onchange_account_id(self):
        super(AccountMoveLine, self).onchange_account_id()
        if self.account_id:
            asset_category = self.account_id.asset_category_id
            if asset_category:
                self.asset_category_id = asset_category.id

    @api.model
    def create(self, vals, check=True):
        if vals.get('asset_id') and not self.env.context.get('allow_asset'):
            raise ValidationError(
                _("You are not allowed to link "
                  "an accounting entry to an asset."
                  "\nYou should generate such entries from the asset."))
        if vals.get('asset_category_id'):
            asset_obj = self.env['account.asset.asset']
            # create asset
            move = self.env['account.move'].browse(vals['move_id'])
            asset_value = vals['debit'] or -vals['credit']
            asset_vals = {
                'name': vals['name'],
                'category_id': vals['asset_category_id'],
                'purchase_value': asset_value,
                'partner_id': vals['partner_id'],
                'date_start': move.date,
            }
            if self.env.context.get('company_id'):
                asset_vals['company_id'] = self.env.context['company_id']
            changed_vals = asset_obj.onchange_category_id(
                vals['asset_category_id'])
            asset_vals.update(changed_vals['value'])
            ctx = dict(self.env.context, create_asset_from_move_line=True,
                       move_id=vals['move_id'])
            asset_id = asset_obj.with_context(**ctx).create(asset_vals)
            vals['asset_id'] = asset_id
        return super(AccountMoveLine, self).create(vals, check)

    @api.multi
    def write(self, vals, check=True, update_check=True):
        for move_line in self:
            if move_line.asset_id.id:
                if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE_LINE):
                    raise ValidationError(
                        _("You cannot change an accounting item "
                          "linked to an asset depreciation line."))
        if vals.get('asset_id'):
            raise ValidationError(
                _("You are not allowed to link "
                  "an accounting entry to an asset."
                  "\nYou should generate such entries from the asset."))
        if vals.get('asset_category_id'):
            if len(self) > 1:
                raise ValidationError(_(
                    'This option should only be used for a single id '
                    'at a time.'))
            asset_obj = self.env['account.asset.asset']
            for aml in self:
                if vals['asset_category_id'] == aml.asset_category_id.id:
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
                changed_vals = asset_obj.onchange_category_id(
                    [], vals['asset_category_id'])
                asset_vals.update(changed_vals['value'])
                ctx = dict(self.env.context, create_asset_from_move_line=True,
                           move_id=aml.move_id.id)
                asset_id = asset_obj.with_context(**ctx).create(asset_vals)
                vals['asset_id'] = asset_id

        return super(AccountMoveLine, self).write(vals, check, update_check)
