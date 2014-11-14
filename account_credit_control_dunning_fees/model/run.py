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
from openerp.osv import orm


class credit_control_run(orm.Model):

    """Add computation of fees"""

    _inherit = "credit.control.run"

    def _generate_credit_lines(self, cr, uid, run_id, context=None):
        """Override method to add fees computation"""
        credit_line_ids = super(credit_control_run,
                                self)._generate_credit_lines(
                                    cr,
                                    uid,
                                    run_id,
                                    context=context)
        fees_model = self.pool['credit.control.dunning.fees.computer']
        fees_model._compute_fees(cr, uid, credit_line_ids, context=context)
        return credit_line_ids
