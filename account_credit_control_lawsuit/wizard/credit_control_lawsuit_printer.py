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
from openerp import models, fields, api, exceptions, _


class CreditControlLawsuitPrinter(models.TransientModel):
    """Print Lawsuit requisition letter

    And manage related credit lines

    """

    _name = "credit.control.lawsuit.printer"
    _rec_name = 'id'

    @staticmethod
    def invoice_filter_key(invoice):
        return any(line for line in invoice.credit_control_line_ids
                   if line.policy_level_id.need_lawsuit)

    @api.model
    def _filter_lawsuit_invoices(self, invoices, key):
        """ Return invoices for which a lawsuit must be filed

        It means that the invoice must be related to an active credit line
        related to a lawsuit policy level

        :param invoices: recordset of invoices to filter

        """
        return invoices.filtered(key)

    @api.model
    def _get_invoices(self):
        """Return invoices ids to be treated from context

        A candidate invoice is related to a credit control line
        with a lawsuit level

        """
        invoice_model = self.env['account.invoice']
        if self.env.context.get('active_model') != 'account.invoice':
            return
        invoice_ids = self.env.context.get('active_ids')
        if not invoice_ids:
            return
        invoices = invoice_model.browse(invoice_ids)
        invoices = self._filter_lawsuit_invoices(invoices,
                                                 self.invoice_filter_key)
        return invoices

    mark_as_filed = fields.Boolean(string='Mark as Filed',
                                   default=True)
    invoice_ids = fields.Many2many(comodel_name='account.invoice',
                                   string='Invoices',
                                   default=_get_invoices)

    @api.model
    def _generate_report(self, invoices):
        """Generate lawsuit requisition report.

        :param invoices: recordset of invoices to print

        :returns: a action to print the report

        """
        report_name = ('account_credit_control_lawsuit.'
                       'report_lawsuit_requisition')
        return self.env['report'].get_action(invoices, report_name)

    @api.model
    def _mark_invoices_as_filed(self, invoices):
        """Mark related credit line of an invoice as overridden.

        Only non lawsuit credit line will be marked

        :param invoice: invoice record to treat

        :returns: marked credit lines
        """
        lines = invoices.mapped('credit_control_line_ids')
        lines = lines.filtered(lambda l: not l.policy_level_id.need_lawsuit)
        lines.write({'manually_overridden': True})
        return lines

    @api.multi
    def print_lawsuit(self):
        """Generate lawsuit requisition report and manage credit lines.

        Non lawsuit credit lines will be overridden

        :returns: an ir.action to print the report

        """
        self.ensure_one()
        invoices = self._filter_lawsuit_invoices(self.invoice_ids,
                                                 self.invoice_filter_key)
        if not invoices:
            raise exceptions.Warning(_('No invoice to print'))
        if self.mark_as_filed:
            self._mark_invoices_as_filed(invoices)
        return self._generate_report(invoices)
