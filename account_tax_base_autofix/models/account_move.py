# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def check_taxes(self, check_taxbase=True, check_sign=True):
        for move in self:
            op_taxs = move.line_ids.filtered(lambda r: r.tax_ids.ids)
            for line in move.line_ids:
                tax = line.tax_line_id
                amount = 0.0
                tax_ids = []
                for op_tax in op_taxs:
                    for tax_line in op_tax.tax_ids:
                        tax_ids.append(tax_line.id)
                        for tax_child in tax_line.children_tax_ids:
                            tax_ids.append(tax_child.id)
                    if tax.id in tax_ids:
                        amount += op_tax.debit-op_tax.credit
                sale = tax.type_tax_use == 'sale'
                purchase = tax.type_tax_use == 'purchase'
                if check_sign:
                    line.tax_sign = ((sale and line.debit - line.credit > 0) or (purchase and line.debit - line.credit < 0)) and -1 or 1
                if check_taxbase and line.tax_base == 0.0 and op_taxs:
                    line.tax_base = abs(amount)
