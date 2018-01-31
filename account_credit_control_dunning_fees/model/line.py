# -*- coding: utf-8 -*-
# Copyright 2014-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class CreditControlLine(models.Model):
    """Add dunning_fees_amount_fees field"""

    _inherit = "credit.control.line"

    dunning_fees_amount = fields.Float(string='Fees')
    balance_due_total = fields.Float(string='Balance due with fees',
                                     compute='compute_balance_due')

    @api.one
    @api.depends('dunning_fees_amount', 'balance_due')
    def compute_balance_due(self):
        self.balance_due_total = self.balance_due + self.dunning_fees_amount
