# -*- coding: utf-8 -*-
# Copyright 2014-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class CreditControlLine(models.Model):
    """Add dunning_fees_amount_fees field"""

    _inherit = "credit.control.line"

    dunning_fees_amount = fields.Float(string='Fees')
    balance_due_total = fields.Float(string='Balance due with fees',
                                     compute='_compute_balance_due')

    @api.multi
    @api.depends('dunning_fees_amount', 'balance_due')
    def _compute_balance_due(self):
        for ln in self:
            ln.balance_due_total = ln.balance_due + ln.dunning_fees_amount
