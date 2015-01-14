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

    @api.model
    def _filter_lawsuit_invoices(self, invoices):
        """ Return invoices for which a lawsuit must be filed

        It means that the invoice must be related to an active credit line
        related to a lawsuit policy level

        :param invoices: recordset of invoices to filter

        """
        return invoices.filtered(lambda invoice: invoice.need_lawsuit)

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
        invoices = self._filter_lawsuit_invoices(invoices)
        return invoices

    @api.model
    def _get_lawsuit_step_id(self):
        step_obj = self.env['account.invoice.lawsuit.step']
        return step_obj.search([('set_when_requisition_printed', '=', True)],
                               limit=1)

    lawsuit_step_id = fields.Many2one(
        comodel_name='account.invoice.lawsuit.step',
        string='Lawsuit Step',
        default=_get_lawsuit_step_id,
    )
    invoice_ids = fields.Many2many(comodel_name='account.invoice',
                                   string='Invoices',
                                   domain=[('need_lawsuit', '=', True)],
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

    @api.multi
    def print_lawsuit(self):
        """Generate lawsuit requisition report and manage credit lines.

        Non lawsuit credit lines will be overridden

        :returns: an ir.action to print the report

        """
        self.ensure_one()
        invoices = self._filter_lawsuit_invoices(self.invoice_ids)
        if not invoices:
            raise exceptions.Warning(_('No invoice to print'))
        if self.lawsuit_step_id:
            # only write if an office is found because otherwise  we will
            # have to print it again
            office_invoices = invoices.filtered(
                lambda invoice: invoice.partner_id.lawsuit_office_id
            )
            office_invoices.write({'lawsuit_step_id': self.lawsuit_step_id.id})
        return self._generate_report(invoices)
