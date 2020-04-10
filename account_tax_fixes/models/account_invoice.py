# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    tag_ids = fields.Many2many(related='tax_id.tag_ids', string='Tags', help="Optional tags you may want to assign for custom reporting")
