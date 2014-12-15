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


class FeesComputer(models.BaseModel):
    """Model that compute dunnig fees.

    This class does not need any database storage as
    it contains pure logic.

    It inherits form ``models.BaseModel`` to benefit of orm facility

    Similar to AbstractModel but log access and actions
    """

    _name = 'credit.control.dunning.fees.computer'
    _auto = False
    _log_access = True
    _register = True
    _transient = False

    @api.model
    def _get_compute_fun(self, level_fees_type):
        """Retrieve function of class that should compute the fees based
        on type

        :param level_fee_type: type existing in model
                               `credit.control.policy.level`
                               for field dunning_fees_type

        :returns: a function of class :class:`FeesComputer`
                 with following signature
                 self, credit_line (record)

        """
        if level_fees_type == 'fixed':
            return self.compute_fixed_fees
        else:
            raise NotImplementedError('fees type %s is not supported' %
                                      level_fees_type)

    @api.model
    def _compute_fees(self, credit_lines):
        """Compute fees for `credit_lines` parameter

        Fees amount is written on credit lines in the field dunning_fees_amount

        :param credit_lines: recordset of `credit.control.line`

        :returns: recordset of `credit.control.line`

        """
        if not credit_lines:
            return credit_lines
        for credit in credit_lines:
            # if there is no dependence between generated credit lines
            # this could be threaded
            self._compute(credit)
        return credit_lines

    @api.model
    def _compute(self, credit_line):
        """Compute fees for a given credit line

        Fees amount is written on credit line in then field dunning_fees_amount

        :param credit_line: credit line record

        :returns: `credit_line` record
        """
        fees_type = credit_line.policy_level_id.dunning_fees_type
        compute = self._get_compute_fun(fees_type)
        fees = compute(credit_line)
        if fees:
            credit_line.write({'dunning_fees_amount': fees})
        return credit_line

    @api.model
    def compute_fixed_fees(self, credit_line):
        """Compute fees amount for fixed fees.
        Correspond to the fixed dunning fees type

        if currency of the fees is not the same as the currency
        of the credit line, fees amount is converted to
        currency of credit line.

        :param credit_line: credit line record

        :return: fees amount float (in credit line currency)

        """
        credit_currency = (credit_line.currency_id or
                           credit_line.company_id.currency_id)
        level = credit_line.policy_level_id
        fees_amount = level.dunning_fixed_amount
        if not fees_amount:
            return 0.0
        fees_currency = (level.dunning_currency_id or
                         level.policy_id.company_id.currency_id)
        if fees_currency == credit_currency:
            return fees_amount
        else:
            return fees_currency.compute(fees_amount, credit_currency)
