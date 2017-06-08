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
    @api.depends('price_unit', 'price_subtotal', 'invoice_id.document_type_id')
    def _compute_report_prices_and_taxes(self):
        for line in self:
            invoice = line.invoice_id
            taxes_included = (
                invoice.document_type_id and
                invoice.document_type_id.get_taxes_included() or False)
            if not taxes_included:
                report_price_unit = line.price_unit
                report_price_subtotal = line.price_subtotal
                not_included_taxes = line.invoice_line_tax_ids
            else:
                included_taxes = line.invoice_line_tax_ids.filtered(
                    lambda x: x in taxes_included)
                not_included_taxes = (
                    line.invoice_line_tax_ids - included_taxes)
                report_price_unit = included_taxes.compute_all(
                    line.price_unit, invoice.currency_id, 1.0, line.product_id,
                    invoice.partner_id)['total_included']
                report_price_subtotal = report_price_unit * line.quantity
            line.report_price_subtotal = report_price_subtotal
            line.report_price_unit = report_price_unit
            line.report_invoice_line_tax_ids = not_included_taxes
