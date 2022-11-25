# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp

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
        # for move in self:
        deprs = self.env['account.asset.line'].search(
            [('move_id', 'in', self.ids),
             ('type', 'in', ['depreciate', 'remove'])])
        if deprs and not self.env.context.get('unlink_from_asset'):
            raise UserError(
                _("You are not allowed to remove an accounting entry "
                  "linked to an asset."
                  "\nYou should remove such entries from the asset."))
        # trigger store function
        deprs.write({'move_id': False})
        return super().unlink()

    @api.multi
    def write(self, vals):
        if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE):
            deprs = self.env['account.asset.line'].search(
                [('move_id', 'in', self.ids), ('type', '=', 'depreciate')])
            if deprs:
                raise UserError(
                    _("You cannot change an accounting entry "
                      "linked to an asset depreciation line."))
        return super().write(vals)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    asset_profile_id = fields.Many2one(comodel_name='account.asset.profile', string='Asset Profile')
    tax_profile_id = fields.Many2one(comodel_name='account.bg.asset.profile', string='Tax Asset Profile')
    asset_id = fields.Many2one(comodel_name='account.asset', string='Asset', ondelete='restrict')
    asset_salvage_value = fields.Float(string='Salvage Value', digits=dp.get_precision('Account'))
    restatement_asset_id = fields.Many2one(comodel_name='account.asset', string='Restatement Asset',
                                           ondelete='restrict')
    restatement_type = fields.Selection(
        selection=lambda self: self.env['account.asset.restatement.value']._selection_method(), default='create')

    # @api.onchange('account_id')
    # def _onchange_account_id(self):
    #     self.asset_profile_id = self.account_id.asset_profile_id

    # def _prepare_asset(self, vals):
    #     self.ensure_one()
    #     move = self.env['account.move'].browse(vals['move_id'])
    #     depreciation_base = vals['debit'] or -vals['credit']
    #     if 'invoice_id' in vals:
    #         invoice_id = self.env['account.invoice'].browse(vals['invoice_id'])
    #     else:
    #         invoice_id = self.invoice_id
    #     return {
    #         'name': vals['name'],
    #         'profile_id': vals.get('asset_profile_id', False),
    #         'tax_profile_id': vals.get('tax_profile_id', False),
    #         'purchase_value': depreciation_base,
    #         'salvage_value': vals.get('asset_salvage_value', False) and vals['asset_salvage_value'],
    #         'partner_id': vals['partner_id'],
    #         'date_start': move.date,
    #         'date_buy': invoice_id and invoice_id.date_invoice or move.date,
    #         'product_id': vals['product_id'],
    #         # 'company_id': vals.get('company_id'),
    #     }

    @api.multi
    def _check_for_assets(self):
        check = {}
        for record in self:
            asset_profile_id = tax_profile_id = False

            if (record.asset_profile_id and not self._context.get('force_asset_all', False)) or not record.product_id:
                # check[record] = record.asset_profile_id
                continue
            # Check in product valuations
            if record.quantity != 1:
                continue
            price_subtotal_signed = (record.debit - record.credit)/record.quantity

            if record.product_id.product_tmpl_id.property_stock_valuation_account:
                asset_profile_id = record.product_id.product_tmpl_id.property_stock_valuation_account.asset_profile_id
                tax_profile_id = record.product_id.product_tmpl_id.property_stock_valuation_account.tax_profile_id

            if not asset_profile_id:
                product_tmpl = record.product_id.product_tmpl_id.categ_id
                if product_tmpl.property_stock_valuation_account_id \
                        and product_tmpl.property_stock_valuation_account_id.asset_profile_id:
                    asset_profile_id = product_tmpl.property_stock_valuation_account_id.asset_profile_id
                    tax_profile_id = product_tmpl.property_stock_valuation_account_id.tax_profile_id

            if asset_profile_id and asset_profile_id.threshold >= price_subtotal_signed:
                if asset_profile_id:
                    asset_profile_id = asset_profile_id.threshold_profile_id
                if tax_profile_id:
                    tax_profile_id = tax_profile_id.threshold_tax_profile_id

            if asset_profile_id or tax_profile_id:
                check[record] = {
                    'asset_profile_id': asset_profile_id.id,
                    'tax_profile_id': tax_profile_id,
                }

            if record.product_id.product_tmpl_id.asset_profile_id or record.product_id.product_tmpl_id.tax_profile_id:
                check[record] = {
                    'asset_profile_id': record.product_id.product_tmpl_id.asset_profile_id,
                    'tax_profile_id': record.product_id.product_tmpl_id.tax_profile_id.id,
                }
        return check

    @api.multi
    def _prepare_asset_create(self, vals):
        debit = 'debit' in vals and vals.get('debit', 0.0) or self.debit
        credit = 'credit' in vals and \
                 vals.get('credit', 0.0) or self.credit
        depreciation_base = debit - credit
        partner_id = 'partner' in vals and \
                     vals.get('partner', False) or self.partner_id.id
        product_id = vals.get('product_id', False) or self.product_id.id

        if 'move_id' in vals:
            move_id = self.env['account.move'].browse(vals['move_id'])
        else:
            move_id = self.move_id

        if 'invoice_id' in vals:
            invoice_id = self.env['account.invoice'].browse(vals['invoice_id'])
        else:
            invoice_id = self.invoice_id

        if vals.get('date', False):
            date_start = vals['date']
        else:
            date_start = self.date

        if not date_start and move_id:
            date_start = move_id.date

        if not date_start and invoice_id:
            date_start = invoice_id.date and invoice_id.date_invoice or invoice_id.date

        if not date_start:
            date_start = fields.Date.today()

        date_start = (fields.Date.from_string(date_start).replace(day=1) + relativedelta(days=31)).replace(day=1)
        date_start = fields.Date.to_string(date_start)
        # _logger.info("DATE START %s:%s" % (date_start, invoice_id))

        return {
            'name': vals.get('name') or self.name,
            'profile_id': vals.get('asset_profile_id', False),
            'tax_profile_id': vals.get('tax_profile_id', False),
            'purchase_value': depreciation_base,
            'partner_id': partner_id,
            'date_start': date_start,
            'product_id': product_id,
            'date_buy': invoice_id and invoice_id.date_invoice or date_start,
            'salvage_value': vals.get('asset_salvage_value', False) and vals['asset_salvage_value'] or self.asset_salvage_value,
            'company_id': vals.get('company_id') or self.company_id.id,
        }

    @api.model
    def create(self, vals):
        if vals.get('asset_id') and not self.env.context.get('allow_asset') and not vals.get('restatement_asset_id'):
            raise UserError(
                _("You are not allowed to link "
                  "an accounting entry to an asset."
                  "\nYou should generate such entries from the asset."))

        if vals.get('restatement_asset_id') and not self.env.context.get('allow_asset'):
            asset = self.env['account.asset'].browse(vals['restatement_asset_id'])
            move = self.env['account.move'].browse(vals['move_id'])
            asset.write({
                'depreciation_restatement_line_ids':
                    [(0, False, asset._value_depreciation_restatement_line(vals, move, move.date,
                                                                           type=vals.get('restatement_type')))]
            })

        if vals.get('asset_profile_id') and not self.env.context.get('allow_asset'):
            # check for additional values added now
            # account = False
            # if vals.get('account_id'):
            #    account = self.env['account.account'].browse(vals['account_id'])
            correction = False
            if vals.get('save_asset_id'):
                correction = True
                vals['asset_id'] = vals['save_asset_id']
                del vals['save_asset_id']

            if not correction:
                # create asset
                asset_obj = self.env['account.asset']
                # _logger.info("ASSET INSIDE %s" % vals)
                temp_vals = self._prepare_asset_create(vals)
                # _logger.info("ASSET INSIDE %s" % temp_vals)
                if vals.get('move_line_id'):
                    temp_vals.update({
                        'move_line_id': vals['move_line_id'],
                    })
                if vals.get('lot_id'):
                    temp_vals.update({
                        'lot_id': vals['lot_id'],
                    })
                if self.env.context.get('company_id'):
                    temp_vals['company_id'] = self.env.context['company_id']
                temp_asset = asset_obj.new(temp_vals)
                temp_asset._onchange_profile_id()
                temp_asset._onchange_tax_profile_id()
                asset_vals = temp_asset._convert_to_write(temp_asset._cache)
                self._get_asset_analytic_values(vals, asset_vals)
                asset = asset_obj.with_context(
                    create_asset_from_move_line=True,
                    move_id=vals['move_id']).create(asset_vals)
                vals['asset_id'] = asset.id
                if vals.get('move_line_id') and 'move_line_id' not in self._fields:
                    del vals['move_line_id']
                if vals.get('lot_id') and 'lot_id' not in self._fields:
                    del vals['lot_id']
        return super(AccountMoveLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if (
                (self.mapped('asset_id') and vals.get('asset_id', False)) and
                set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE_LINE)
                and not (
                self.env.context.get('allow_asset_removal') and
                list(vals.keys()) == ['asset_id'])
        ):
            raise UserError(
                _("You cannot change an accounting item line "
                  "linked to an asset depreciation line."))
        if vals.get('asset_id') and not self.env.context.get('allow_asset') and not vals.get('restatement_asset_id'):
            raise UserError(
                _("You are not allowed to link "
                  "an accounting entry to an asset."
                  "\nYou should generate such entries from the asset."))
        if vals.get('restatement_asset_id') and not self.env.context.get('allow_asset'):
            asset = self.env['account.asset'].browse(vals['restatement_asset_id'])
            asset.write({
                'depreciation_restatement_line_ids':
                    [(0, False, asset._value_depreciation_restatement_line(
                        vals,
                        self.move_id,
                        self.date,
                        type=vals.get('restatement_type', self.restatement_type)))]
            })
        if vals.get('asset_profile_id') and not self.env.context.get('allow_asset'):
            if len(self) == 1:
                raise AssertionError(_(
                    'This option should only be used for a single id at a '
                    'time.'))
            asset_obj = self.env['account.asset']
            # check for additional values added now
            correction = False
            if vals.get('refund_invoice_id') or self.refund_invoice_id:
                refund_invoice_id = vals.get('refund_invoice_id') or self.refund_invoice_id
                assets = asset_obj.search([('type', '=', 'normal')])
                for asset in assets:
                    if refund_invoice_id in asset.account_move_line_ids.mapped('invoice_id').ids:
                        correction = True
                        break
            if not correction:
                for aml in self:
                    if vals['asset_profile_id'] == aml.asset_profile_id.id:
                        continue
                    # create asset
                    asset_vals = aml._prepare_asset_create(vals)
                    self._play_onchange_profile_id(asset_vals)
                    self._get_asset_analytic_values(vals, asset_vals)
                    asset = asset_obj.with_context(
                        create_asset_from_move_line=True,
                        move_id=aml.move_id.id).create(asset_vals)
                    vals['asset_id'] = asset.id
        return super(AccountMoveLine, self).write(vals)

    @api.model
    def _get_asset_analytic_values(self, vals, asset_vals):
        asset_vals['account_analytic_id'] = vals.get(
            'analytic_account_id', False)

    @api.model
    def _play_onchange_profile_id(self, vals):
        asset_obj = self.env['account.asset']
        asset_temp = asset_obj.new(vals)
        asset_temp._onchange_profile_id()
        for field in asset_temp._fields:
            if field not in vals and asset_temp[field]:
                vals[field] = asset_temp._fields[field]. \
                    convert_to_write(asset_temp[field], asset_temp)
