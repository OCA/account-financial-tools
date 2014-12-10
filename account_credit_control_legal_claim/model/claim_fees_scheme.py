# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
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
from operator import attrgetter
from openerp import models, fields, api


class ClaimFeesScheme(models.Model):
    """Claim fees

    Claim offices take fees based on the open amount
    when a legal action is taken.

    The model represent the scheme open amount/fees

    """

    _name = 'legal.claim.fees.scheme'

    @api.model
    def _company_get(self):
        """Return related company"""
        company_obj = self.env['res.company']
        return company_obj._company_default_get('claim.fees.scheme')

    name = fields.Char(required=True)
    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product',
                                 required=True)
    claim_scheme_line_ids = fields.One2many(
        comodel_name='legal.claim.fees.scheme.line',
        inverse_name='claim_scheme_id',
        string='Price lists')
    company_id = fields.Many2one(comodel_name='res.company',
                                 string='Company',
                                 default=_company_get)
    currency_id = fields.Many2one(comodel_name='res.currency',
                                  string='Currency',
                                  required=True)

    @api.model
    def _due_from_invoices(self, invoices):
        """Compute due amount form a list of invoice

        :param invoices: recordset of invoices

        :returns: due amount (float)

        """
        return sum(x.residual for x in invoices)

    @api.multi
    def get_fees_from_amount(self, due_amount):
        """Get the fees from open amount

        :param due_amount: float of the open (due) amount

        :returns: fees amount (float)

        """
        self.ensure_one()
        lines = self.claim_scheme_line_ids
        lines = lines.sorted(key=attrgetter('open_amount'), reverse=True)
        for line in lines:
            if due_amount >= line.open_amount:
                return line.fees
        return lines[-1].fees

    @api.multi
    def get_fees_from_invoices(self, invoice_ids):
        """Get the fees form a list of invoices

        :param invoice_ids: list of invoice ids

        :returns: fees amount (float)

        """
        self.ensure_one()
        invoices = self.env['account.invoice'].browse(invoice_ids)
        return self._get_fees_from_invoices(invoices)

    @api.multi
    def _get_fees_from_invoices(self, invoices):
        """Get the fees form a recordset of invoices

        :param invoice_ids: recordset of invoices

        :returns: fees amount (float)

        """
        self.ensure_one()
        due = self._due_from_invoices(invoices)
        return self.get_fees_from_amount(due)


class ClaimFeesSchemeLine(models.Model):
    """Price list line of scheme that contains price and qty"""

    _name = 'legal.claim.fees.scheme.line'
    _rec_name = "open_amount"
    _order = "open_amount"

    claim_scheme_id = fields.Many2one(comodel_name='legal.claim.fees.scheme',
                                      string='Price list',
                                      required=True)
    open_amount = fields.Integer(string='Open Amount', required=True)
    fees = fields.Float(string='Fees', required=True)
