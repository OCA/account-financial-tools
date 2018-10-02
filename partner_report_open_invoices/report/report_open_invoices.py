# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import time

from openerp.report import report_sxw
from openerp import models


class ReportOpenInvoicesParser(report_sxw.rml_parse):

    def __init__(self, name):
        super(ReportOpenInvoicesParser, self).__init__(name)
        ids = self.env.context.get('active_ids')
        partner_obj = self.env['res.partner']
        docs = partner_obj.browse(ids)

        addresses = docs._address_display(None, None)
        self.localcontext.update({
            'docs': docs,
            'time': time,
            'message': self._message,
            'getLinesReceivable': self._lines_get_receivable,
            'getLinesPayable': self._lines_get_payable,
            'addresses': addresses,
        })

    def _lines_get_receivable(self, partner):
        inv_obj = self.env['account.invoice']
        dom = [('partner_id', '=', partner.id),
               ('account_id.type', '=', 'receivable'),
               ('state', '=', 'open')]
        inv_rec = inv_obj.search(dom)
        move_lines = []
        for invoice in inv_rec:
            for move_line_data in invoice.move_id.line_id:
                if move_line_data.date_maturity:
                    move_lines.append(move_line_data)
        return move_lines

    def _lines_get_payable(self, partner):
        inv_obj = self.env['account.invoice']
        dom = [('partner_id', '=', partner.id),
               ('account_id.type', '=', 'payable'),
               ('state', '=', 'open')]
        inv_rec = inv_obj.search(dom)
        move_lines = []
        for invoice in inv_rec:
            for move_line_data in invoice.move_id.line_id:
                if move_line_data.date_maturity:
                    move_lines.append(move_line_data)
        return move_lines

    def _message(self, obj, company):
        return company.open_invoices_msg.split('\n')


class ReportOpenInvoices(models.AbstractModel):
    _name = 'report.partner_report_open_invoices.report_open_invoices'
    _inherit = 'report.abstract_report'
    _template = 'partner_report_open_invoices.report_open_invoices'
    _wrapped_report_class = ReportOpenInvoicesParser
