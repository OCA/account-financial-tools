# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _

import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    @api.onchange('amount')
    def _onchange_amount(self):
        if not self.manual and self._context.get("force_manual", False):
            self.manual = True
