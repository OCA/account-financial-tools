# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import copy

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super().finalize_invoice_move_lines(move_lines)
        new_lines = []
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
        return move_lines

    @api.multi
    def action_move_create(self):
        res = super().action_move_create()
        for inv in self:
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
            assets |= move.line_ids.mapped('asset_id')
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
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    asset_profile_id = fields.Many2one(
        comodel_name='account.asset.profile',
        string='Asset Profile')
    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        domain=[('state', 'in', ['open', 'close'])],
        help="Complete this field when selling an asset "
             "in order to facilitate the creation of the "
             "asset removal accounting entries via the "
             "asset 'Removal' button")

    @api.onchange('account_id')
    def _onchange_account_id(self):
        self.asset_profile_id = self.account_id.asset_profile_id.id
        return super()._onchange_account_id()
