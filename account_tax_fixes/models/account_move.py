# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    use_refund = fields.Boolean('Refund/Discount', help='Please checked it if is refund or discount',
                                compute="_compute_use_refund")

    @api.multi
    def _compute_use_refund(self):
        for record in self:
            if any(x.id for x in record.line_ids if x.invoice_id and x.invoice_id.type in ['in_refund', 'out_refund']) \
                    or any(x.id for x in record.line_ids if x.tax_sign == -1):
                record.use_refund = True
            else:
                record.use_refund = False

    @api.multi
    def toggle_use_refund(self):
        for record in self:
            record.use_refund = not record.use_refund
            for line in record.line_ids:
                if line.invoice_id and line.invoice_id.type in ['in_refund', 'out_refund']\
                        and (line.tax_ids or line.tax_line_id) and line.tax_sign == 1:
                    line.tax_sign = -1
                elif line.invoice_id and line.invoice_id.type in ['in_invoice', 'out_invoice'] \
                        and (line.tax_ids or line.tax_line_id) and line.tax_sign == -1:
                    line.tax_sign = 1

                if record.use_refund and (line.tax_ids or line.tax_line_id) and not line.invoice_id:
                    line.tax_sign = -1
                elif not record.use_refund and (line.tax_ids or line.tax_line_id) and not line.invoice_id:
                    line.tax_sign = 1
            self._compute_use_refund()
