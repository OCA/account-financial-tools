# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


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
