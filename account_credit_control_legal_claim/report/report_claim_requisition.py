# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
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

from itertools import groupby
from openerp import models, api, fields

report_name = 'account_credit_control_legal_claim.report_claim_requisition'


class ClaimRequisitionPartner(models.TransientModel):
    _name = 'claim.requisition.partner'

    partner = fields.Many2one(comodel_name='res.partner')
    invoices = fields.Many2many(comodel_name='account.invoice')
    currency = fields.Many2one(comodel_name='res.currency')
    dunning_fees = fields.Float(compute='compute_dunning_fees')
    due_amount = fields.Float(compute='compute_due_amount')
    claim_fees = fields.Float(compute='compute_claim_fees')
    paid_amount = fields.Float(compute='compute_paid_amount')

    def _active_line(self, line):
        return (line.state not in ('draft', 'ignored') and
                not line.manually_overridden)

    @api.depends('invoices')
    def compute_dunning_fees(self):
        lines = self.invoices.mapped('credit_control_line_ids')
        self.dunning_fees = sum(line.dunning_fees_amount for line in lines
                                if self._active_line(line))

    @api.depends('invoices', 'partner')
    def compute_claim_fees(self):
        scheme = self.partner.claim_office_id.fees_scheme_id
        self.claim_fees = scheme._get_fees_from_invoices(self.invoices)

    @api.depends('invoices')
    def compute_due_amount(self):
        self.due_amount = sum(invoice.residual for invoice in self.invoices)

    @api.depends('invoices')
    def compute_paid_amount(self):
        self.paid_amount = sum(inv.amount_total - inv.residual
                               for inv in self.invoices)


class ClaimRequisitionReport(models.AbstractModel):
    _name = 'report.%s' % report_name

    @api.model  # 'ids' are ids of invoices, hence the 'model' decorator
    def render_html(self, ids, data=None):
        invoice_obj = self.env['account.invoice']
        invoices = invoice_obj.browse(ids)

        report_partner_obj = self.env['claim.requisition.partner']
        report_partners = report_partner_obj.browse()
        grouped = groupby(invoices, lambda inv: (inv.partner_id,
                                                 inv.currency_id))
        for (partner, currency), invoices in grouped:
            report_partner = report_partner_obj.create({})
            report_partner.partner = partner
            report_partner.currency = currency
            report_partner.invoices = invoice_obj.browse(inv.id for inv
                                                         in invoices)
            report_partners += report_partner

        docargs = {
            'doc_ids': report_partners.ids,
            'doc_model': 'claim.requisition.partner',
            'docs': report_partners,
        }
        # Use the old API because the render() has an 'ids' argument
        # but it contains records of another model. The API wrapper
        # think it is a 'multi' method whereas it is a 'model' one.
        report_obj = self.pool['report']
        html = report_obj.render(self.env.cr, self.env.uid,
                                 ids, report_name,
                                 docargs, context=self.env.context)
        return html
