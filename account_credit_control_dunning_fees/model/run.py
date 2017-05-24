# -*- coding: utf-8 -*-
# Copyright 2014-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class CreditControlRun(models.Model):
    """Add computation of fees"""

    _inherit = "credit.control.run"

    @api.multi
    @api.returns('credit.control.line')
    def _generate_credit_lines(self):
        """Override method to add fees computation"""
        credit_lines = super(CreditControlRun, self)._generate_credit_lines()
        fees_model = self.env['credit.control.dunning.fees.computer']
        fees_model._compute_fees(credit_lines)
        return credit_lines
