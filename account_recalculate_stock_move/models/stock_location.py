# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    valuation_in_account_id = fields.Many2one('account.account', 'Stock Valuation Account (Incoming)', company_dependent=True)
    valuation_out_account_id = fields.Many2one('account.account', 'Stock Valuation Account (Outgoing)', company_dependent=True)
