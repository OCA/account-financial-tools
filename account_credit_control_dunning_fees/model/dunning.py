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


class FeesComputer(orm.BaseModel):

    """Model that compute dunnig fees.

    This class does not need any database storage as
    it contains pure logic.

    It inherits form ``orm.BaseModel`` to benefit of orm facility

    Similar to AbstractModel but log access and actions
    """

    _name = 'credit.control.dunning.fees.computer'
    _auto = False
    _log_access = True
    _register = True
    _transient = False

    def _get_compute_fun(self, level_fees_type):
        """Retrieve function of class that should compute the fees based on type

        :param level_fee_type: type exisiting in model
                               `credit.control.policy.level`
                               for field dunning_fees_type

        :returns: a function of class :class:`FeesComputer`
                 with following signature
                 self, cr, uid, credit_line (record), context

        """
        if level_fees_type == 'fixed':
            return self.compute_fixed_fees
        else:
            raise NotImplementedError('fees type %s is not supported' %
                                      level_fees_type)

    def _compute_fees(self, cr, uid, credit_line_ids, context=None):
        """Compute fees for `credit_line_ids` parameter

        Fees amount is written on credit line in field dunning_fees_amount

        :param credit_line_ids: list of `credit.control.line` ids

        :returns: `credit_line_ids` list of `credit.control.line` ids

        """
        if context is None:
            context = {}
        if not credit_line_ids:
            return credit_line_ids
        c_model = self.pool['credit.control.line']
        credit_lines = c_model.browse(cr, uid, credit_line_ids,
                                      context=context)
        for credit in credit_lines:
            # if there is no dependence between generated credit lines
            # this could be threaded
            self._compute(cr, uid, credit, context=context),
        return credit_line_ids

    def _compute(self, cr, uid, credit_line, context=None):
        """Compute fees for a given credit line

        Fees amount is written on credit line in field dunning_fees_amount

        :param credit_line: credit line record

        :returns: `credit_line` record
        """
        fees_type = credit_line.policy_level_id.dunning_fees_type
        compute = self._get_compute_fun(fees_type)
        fees = compute(cr, uid, credit_line, context=context)
        if fees:
            credit_line.write({'dunning_fees_amount': fees},
                              context=context)
        return credit_line

    def compute_fixed_fees(self, cr, uid, credit_line, context=None):
        """Compute fees amount for fixed fees.
        Correspond to the fixed dunning fees type

        if currency of the fees is not the same as the currency
        of the credit line, fees amount is converted to
        currency of credit line.

        :param credit_line: credit line record

        :return: fees amount float (in credit line currency)

        """
        currency_model = self.pool['res.currency']
        credit_currency = credit_line.currency_id
        level = credit_line.policy_level_id
        fees_amount = level.dunning_fixed_amount
        if not fees_amount:
            return 0.0
        fees_currency = level.dunning_currency_id
        if fees_currency == credit_currency:
            return fees_amount
        else:
            return currency_model.compute(cr, uid, fees_currency.id,
                                          credit_currency.id, fees_amount,
                                          context=context)
