# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api
# from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    report_price_unit = fields.Monetary(
        string='Unit Price',
        compute='_compute_report_prices_and_taxes'
        )
    report_price_subtotal = fields.Monetary(
        string='Amount',
        compute='_compute_report_prices_and_taxes'
        )
    report_invoice_line_tax_ids = fields.One2many(
        compute="_compute_report_prices_and_taxes",
        comodel_name='account.tax',
        string='Taxes'
        )

    @api.multi
    @api.depends('price_unit', 'price_subtotal')
    def _compute_report_prices_and_taxes(self):
        for line in self:
            included_tax_group_ids = (
                line.invoice_id.document_letter_id.included_tax_group_ids)
            if not included_tax_group_ids:
                report_price_unit = line.price_unit
                report_price_subtotal = line.price_subtotal
                not_included_taxes = line.invoice_line_tax_ids
            else:
                currency = (
                    line.invoice_id and line.invoice_id.currency_id or None)
                included_taxes = line.invoice_line_tax_ids.filtered(
                    lambda x: x.tax_group_id in included_tax_group_ids)
                not_included_taxes = (
                    line.invoice_line_tax_ids - included_taxes)
                report_price_unit = included_taxes.compute_all(
                    line.price_unit, currency, 1.0, line.product_id,
                    line.invoice_id.partner_id)['total_included']
                report_price_subtotal = report_price_unit * line.quantity
            line.report_price_subtotal = report_price_subtotal
            line.report_price_unit = report_price_unit
            line.report_invoice_line_tax_ids = not_included_taxes
