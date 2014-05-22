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
from openerp.osv import orm, fields


class claim_fees_scheme(orm.Model):
    """Claim fees

    Claim offices  take fees based on open amount
    whan a legal action is taken.

    The model represent the scheme open amount/fees

    """

    _name = 'legal.claim.fees.scheme'

    _columns = {
        'name': fields.char('Name',
                            required=True),
        'product_id': fields.many2one('product.product',
                                      'Product',
                                      required=True),
        'claim_scheme_line_ids': fields.one2many('legal.claim.fees.scheme.line',
                                                 'claim_scheme_id',
                                                 'Price lists'),
        'company_id': fields.many2one('res.company',
                                      'Company'),
        'currency_id': fields.many2one('res.currency',
                                       'Currency',
                                       required=True),
    }

    def _company_get(self, cr, uid, context=None):
        """Return related company"""
        return self.pool['res.company']._company_default_get(cr, uid,
                                                             'claim.fees.scheme',
                                                             context=context)
    _defaults = {'company_id': _company_get}

    def _due_from_invoices(self, invoices_records, context=None):
        """Compute due amount form a list of invoice

        :param invoices_record: list of invoice records

        :returns: due amount (float)

        """
        return sum(x.residual for x in invoices_records)

    def _get_fees_from_amount(self, cr, uid, ids, due_amount, context=None):
        """Get the fees from open amount

        :param due_amount: float of the open (due) amount

        :returns: fees amount (float)

        """
        assert len(ids) == 1, 'Only on id expected'
        current = self.browse(cr, uid, ids[0], context=context)
        lines = current.claim_scheme_line_ids
        lines.sort(key=attrgetter('open_amount'), reverse=True)
        for line in lines:
            if due_amount >= line.open_amount:
                return line.fees
        return lines[-1].fees

    def get_fees_from_invoices(self, cr, uid, ids, invoice_ids, context=None):
        """Get the fees form a list of invoice

        :param invoice_ids: list of invoice_ids

        :returns: fees amount (float)

        """
        assert len(ids) == 1, 'Only on id expected'
        invoices = self.pool['account.invoice'].browse(cr, uid, invoice_ids,
                                                       context=context)
        current = self.browse(cr, uid, ids[0], context=context)
        due = self._due_from_invoices(invoices, context=context)
        return current._get_fees_from_amount(due)


class claim_fees_scheme_line(orm.Model):
    """Price list line of scheme
    that contains price and qty"""

    _name = 'legal.claim.fees.scheme.line'
    _rec_name = "open_amount"
    _order = "open_amount"

    _columns = {
        'claim_scheme_id': fields.many2one('legal.claim.fees.scheme',
                                           'Price list',
                                           required=True),
        'open_amount': fields.integer('Open Amount',
                                      required=True),
        'fees': fields.float('Fees',
                             required=True),
    }
