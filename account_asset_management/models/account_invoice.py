# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import copy
from statistics import mean

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    count_assets = fields.Integer('Count assets', compute='_compute_count_assets')

    @api.multi
    def _compute_count_assets(self):
        for record in self:
            record.count_assets = len(record.invoice_line_ids._check_for_assets())

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super().finalize_invoice_move_lines(move_lines)
        for inv in self:
            new_lines = []
            # check for refund to cancel new assets
            assets = False
            if inv.refund_invoice_id:
                move = inv.refund_invoice_id.move_id
                assets = move.line_ids.mapped('asset_id')
            for line_tuple in move_lines:
                line = line_tuple[2]
                dp = self.env['decimal.precision']
                if line.get('asset_profile_id') and \
                        line.get('quantity', 0.0) > 1.0:
                    profile = self.env['account.asset.profile'].browse(
                        [line.get('asset_profile_id')])
                    if profile.asset_product_item:
                        origin_line = copy.deepcopy(line)
                        line_qty = line.get('quantity')
                        line['quantity'] = round(line['quantity'] / line_qty,
                                                 dp.precision_get('Account'))
                        line['debit'] = round(line['debit'] / line_qty,
                                              dp.precision_get('Account'))
                        line['credit'] = round(line['credit'] / line_qty,
                                               dp.precision_get('Account'))
                        if assets:
                            asset = assets[0]
                            line['save_asset_id'] = asset.id
                            asset.write({'depreciation_restatement_line_ids': [(0, False, {'asset_id': asset.id,
                                                                                           'name': asset._get_depreciation_entry_name(0),
                                                                                           'type': 'create',
                                                                                           'move_id': self.move_id.id,
                                                                                           'init_entry': True,
                                                                                           'line_date': self.refund_invoice_id.date_invoice,
                                                                                           'depreciation_base': line['debit'] - line['credit']})]})
                        for analytic_line_tuple in line['analytic_line_ids']:
                            analytic_line = analytic_line_tuple[2]
                            analytic_line['amount'] = round(
                                analytic_line['amount'] / line_qty,
                                dp.precision_get('Account'))
                            analytic_line['unit_amount'] = round(
                                analytic_line['unit_amount'] / line_qty, 2)
                        line_to_create = line_qty
                        while line_to_create > 1:
                            line_to_create -= 1
                            new_line = copy.deepcopy(line_tuple)
                            if assets:
                                inx = int(line_to_create)
                                if inx in range(-len(assets), len(assets)):
                                    asset = assets[inx]
                                    new_line[2]['save_asset_id'] = asset.id
                                    asset.write({'depreciation_restatement_line_ids': [(0, False, {'asset_id': asset.id,
                                               'name': asset._get_depreciation_entry_name(0),
                                               'type': 'create',
                                               'move_id': self.move_id.id,
                                               'init_entry': True,
                                               'line_date': self.refund_invoice_id.date_invoice,
                                               'depreciation_base': new_line[2]['debit'] - new_line[2]['credit']})]})
                            #_logger.info("ASSETS %s" % new_line[2])
                            new_lines.append(new_line)
                        # Compute rounding difference and apply it on the first
                        # line
                        line['quantity'] += round(
                            origin_line['quantity'] - line['quantity'] * line_qty,
                            2)
                        line['debit'] += round(
                            origin_line['debit'] - line['debit'] * line_qty,
                            dp.precision_get('Account'))
                        line['credit'] += round(
                            origin_line['credit'] - line['credit'] * line_qty,
                            dp.precision_get('Account'))
                        i = 0
                        for analytic_line_tuple in line['analytic_line_ids']:
                            analytic_line = analytic_line_tuple[2]
                            origin_analytic_line = \
                                origin_line['analytic_line_ids'][i][2]
                            analytic_line['amount'] += round(
                                origin_analytic_line['amount'] - analytic_line[
                                    'amount'] * line_qty,
                                dp.precision_get('Account'))
                            analytic_line['unit_amount'] += round(
                                origin_analytic_line['unit_amount'] -
                                analytic_line[
                                    'unit_amount'] * line_qty,
                                dp.precision_get('Account'))
                            i += 1
            move_lines.extend(new_lines)
        _logger.info("DATA %s" % move_lines)
        return move_lines

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            assets = False
            # check for refund to cancel new assets
            if inv.refund_invoice_id:
                move = inv.refund_invoice_id.move_id
                assets = move.line_ids.mapped('asset_id')
            if not assets:
                assets = inv.move_id.line_ids.mapped('asset_id')
                for asset in assets:
                    asset.code = inv.move_name
                    asset_line_name = asset._get_depreciation_entry_name(0)
                    asset.depreciation_line_ids[0].with_context(
                        {'allow_asset_line_update': True}
                    ).name = asset_line_name
        return res

    @api.multi
    def action_cancel(self):
        assets = self.env['account.asset']
        for inv in self:
            move = inv.move_id
            assets |= move.line_ids.filtered(lambda r: r.invoice_id.id == inv.id).mapped('asset_id')
            depreciation_restatement_line = self.env['account.asset.restatement.value'].search([('move_id', '=', move.id)])
            if depreciation_restatement_line:
                depreciation_restatement_line.unlink()
        super().action_cancel()
        if assets:
            assets.unlink()
        return True

    @api.model
    def line_get_convert(self, line, part):
        res = super().line_get_convert(line, part)
        if line.get('asset_profile_id'):
            # skip empty debit/credit
            if res.get('debit') or res.get('credit'):
                res['asset_profile_id'] = line['asset_profile_id']
        if line.get('tax_profile_id'):
            # skip empty debit/credit
            if res.get('debit') or res.get('credit'):
                res['tax_profile_id'] = line['tax_profile_id']
        return res

    @api.model
    def inv_line_characteristic_hashcode(self, invoice_line):
        res = super().inv_line_characteristic_hashcode(
            invoice_line)
        res += '-%s' % invoice_line.get('asset_profile_id', 'False')
        return res

    @api.model
    def invoice_line_move_line_get(self):
        res = super().invoice_line_move_line_get()
        invoice_line_obj = self.env['account.invoice.line']
        for vals in res:
            if vals.get('invl_id'):
                invline = invoice_line_obj.browse(vals['invl_id'])
                if invline.asset_profile_id:
                    vals['asset_profile_id'] = invline.asset_profile_id.id
                    vals['tax_profile_id'] = invline.tax_profile_id.id
                    vals['asset_salvage_value'] = invline.asset_salvage_value
        return res

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        if line.asset_profile_id:
            data['asset_profile_id'] = line.asset_profile_id.id
        return data

    def _action_invoice_rebuild_pre(self):
        result = super()._action_invoice_rebuild_pre()
        assets = self.env['account.asset']
        # Remove all assets from move_id
        move = self.move_id
        assets |= move.line_ids.filtered(lambda r: r.invoice_id.id == self.id).mapped('asset_id')
        depreciation_restatement_line = self.env['account.asset.restatement.value'].search(
            [('move_id', '=', move.id)])
        if depreciation_restatement_line:
            depreciation_restatement_line.unlink()
        if assets:
            assets.unlink()
        #_logger.info("ASSET %s" % self.type)
        if self.type in ('in_invoice', 'in_refund'):
            for line in self.invoice_line_ids:
                line._onchange_account_id()
                #_logger.info("LINE ASSET %s" % line)
        # add check for sallied assets
        return result

    def action_add_asset(self):
        wizard = self.env['account.invoice.asset'].create({
            'invoice_id': self.id,
            'move_id': self.move_id.id,
            'move_line_ids': [(4, r.id) for r in self.move_id.mapped('line_ids')],
        })
        invoice = wizard.invoice_id
        for line in invoice.invoice_line_ids:
            if not line.asset_profile_id:
                line._onchange_account_id()
            if line.asset_profile_id:
                wizard.invoice_line_ids += wizard.invoice_line_ids.new({
                    'invoice_line_id': line.id,
                    # 'product_id': line.product_id.id,
                    # 'account_id': line.account_id.id,
                })
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.invoice.asset",
            "res_id": wizard.id,
            "views": [[False, "form"], [False, "tree"]],
            "view_mode": 'tree,form',
            "view_id": self.env.ref('account_asset_management.account_invoice_asset_view_form').id,
            "target": "new",
        }


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    asset_profile_id = fields.Many2one(
        comodel_name='account.asset.profile',
        string='Asset Profile')
    tax_profile_id = fields.Many2one(
        comodel_name='account.bg.asset.profile',
        string='Tax Asset Profile')
    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        domain=[('type', '=', 'normal'),
                ('state', 'in', ['open', 'close'])],
        help="Complete this field when selling an asset "
             "in order to facilitate the creation of the "
             "asset removal accounting entries via the "
             "asset 'Removal' button")
    asset_salvage_value = fields.Float(string='Salvage Value', digits=dp.get_precision('Account'))

    @api.multi
    def _check_for_assets(self):
        check = {}
        for record in self:
            if record.asset_profile_id:
                check[record] = record.asset_profile_id
                continue
            # Check in product valuations
            product_tmpl = record.product_id.product_tmpl_id.categ_id
            if product_tmpl.property_stock_valuation_account_id and product_tmpl.property_stock_valuation_account_id.asset_profile_id:
                check[record] = product_tmpl.property_stock_valuation_account_id.asset_profile_id

            # override with account from line
            if record.account_id.asset_profile_id:
                check[record] = record.account_id.asset_profile_id
        return check

    @api.onchange('account_id')
    def _onchange_account_id(self):
        price_subtotal_signed = self.price_unit
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.with_context(
                date=self.invoice_id._get_currency_rate_date()).compute(price_subtotal_signed,
                                                                        self.invoice_id.company_id.currency_id)
        # Check in product valuations
        product_tmpl = self.product_id.product_tmpl_id.categ_id
        if product_tmpl.property_stock_valuation_account_id and product_tmpl.property_stock_valuation_account_id.asset_profile_id:
            self.asset_profile_id = product_tmpl.property_stock_valuation_account_id.asset_profile_id
            if product_tmpl.property_stock_valuation_account_id.asset_profile_id.threshold >= price_subtotal_signed:
                self.asset_profile_id = product_tmpl.property_stock_valuation_account_id.asset_profile_id.threshold_profile_id

        if product_tmpl.property_stock_valuation_account_id and product_tmpl.property_stock_valuation_account_id.tax_profile_id:
            self.tax_profile_id = product_tmpl.property_stock_valuation_account_id.tax_profile_id
            if product_tmpl.property_stock_valuation_account_id.tax_profile_id.threshold >= price_subtotal_signed:
                self.tax_profile_id = product_tmpl.property_stock_valuation_account_id.tax_profile_id.threshold_tax_profile_id

        # override with account from line
        if self.account_id.asset_profile_id:
            self.asset_profile_id = self.account_id.asset_profile_id
            if self.account_id.asset_profile_id.threshold >= price_subtotal_signed:
                self.asset_profile_id = self.account_id.asset_profile_id.threshold_profile_id

        if self.account_id.tax_profile_id:
            self.tax_profile_id = self.account_id.tax_profile_id
            if self.account_id.tax_profile_id.threshold >= price_subtotal_signed:
                self.tax_profile_id = self.account_id.tax_profile_id.threshold_tax_profile_id
        #_logger.info("ACCOUNT ONCHANGE %s:%s:%s:%s:%s:%s" % (self, price_subtotal_signed, product_tmpl, product_tmpl.property_stock_valuation_account_id, product_tmpl.property_stock_valuation_account_id and product_tmpl.property_stock_valuation_account_id.tax_profile_id, self.account_id.asset_profile_id))
        return super()._onchange_account_id()

    @api.onchange('product_id')
    def _onchange_product_id(self):
        ret = super(AccountInvoiceLine, self)._onchange_product_id()
        self._onchange_account_id()
        return ret
