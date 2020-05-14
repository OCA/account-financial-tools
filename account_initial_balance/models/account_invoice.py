# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    is_initial_balance = fields.Boolean('This is initial balance')
