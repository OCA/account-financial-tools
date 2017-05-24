# -*- coding: utf-8 -*-
# Copyright 2014-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class CreditCommunication(models.TransientModel):
    _inherit = 'credit.control.communication'

    @api.model
    def _get_total_due(self):
        balance_field = 'credit_control_line_ids.balance_due_total'
        return sum(self.mapped(balance_field))
