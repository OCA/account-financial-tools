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
from openerp import models, api


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
