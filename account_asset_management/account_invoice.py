# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _

import copy


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        move_lines = super(AccountInvoice, self)\
            .finalize_invoice_move_lines(move_lines)
        new_lines = []
        for line_tuple in move_lines:
            line = line_tuple[2]
            dp = self.env['decimal.precision']
            if line.get('asset_category_id') and \
                            line.get('quantity', 0.0) > 1.0:
                categ = self.env['account.asset.category'].browse(
                    [line.get('asset_category_id')])
                if categ.asset_product_item:
                    origin_line = copy.deepcopy(line)
                    line_qty = line.get('quantity')
                    line['quantity'] = round(line['quantity'] / line_qty,
                                             dp.precision_get('Account'))
                    line['debit'] = round(line['debit'] / line_qty,
                                          dp.precision_get('Account'))
                    line['credit'] = round(line['credit'] / line_qty,
                                           dp.precision_get('Account'))
                    line['tax_amount'] = round(line['tax_amount'] / line_qty,
                                               dp.precision_get('Account'))
                    for analytic_line_tuple in line['analytic_lines']:
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
                    line['tax_amount'] += round(
                        origin_line['tax_amount'] - line[
                            'tax_amount'] * line_qty,
                        dp.precision_get('Account'))
                    i = 0
                    for analytic_line_tuple in line['analytic_lines']:
                        analytic_line = analytic_line_tuple[2]
                        origin_analytic_line = \
                        origin_line['analytic_lines'][i][2]
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
