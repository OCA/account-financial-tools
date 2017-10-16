# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from openerp.report import report_sxw
from openerp import models


class report_open_invoices_parser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_open_invoices_parser, self).__init__(
            cr, uid, name, context=context)
        ids = context.get('active_ids')
        partner_obj = self.pool['res.partner']
        docs = partner_obj.browse(cr, uid, ids, context)

        addresses = self.pool['res.partner']._address_display(
            cr, uid, ids, None, None)
        self.localcontext.update({
            'docs': docs,
            'time': time,
            'message': self._message,
            'getLinesReceivable': self._lines_get_receivable,
            'getLinesPayable': self._lines_get_payable,
            'addresses': addresses,
        })
        self.context = context

    def _lines_get_receivable(self, partner):
        inv_obj = self.pool['account.invoice']
        dom = [('partner_id', '=', partner.id),
               ('account_id.type', '=', 'receivable'),
               ('state', '=', 'open')]
        inv_rec = inv_obj.search(self.cr, self.uid, dom)
        move_lines = []
        for invoice in inv_rec:
            for invoice_data in inv_obj.browse(self.cr, self.uid, invoice):
                for move_line_data in invoice_data.move_id.line_id:
                    if move_line_data.date_maturity:
                        move_lines.append(move_line_data)
        return move_lines

    def _lines_get_payable(self, partner):
        inv_obj = self.pool['account.invoice']
        dom = [('partner_id', '=', partner.id),
               ('account_id.type', '=', 'payable'),
               ('state', '=', 'open')]
        inv_rec = inv_obj.search(self.cr, self.uid, dom)
        move_lines = []
        for invoice in inv_rec:
            for invoice_data in inv_obj.browse(self.cr, self.uid, invoice):
                for move_line_data in invoice_data.move_id.line_id:
                    if move_line_data.date_maturity:
                        move_lines.append(move_line_data)
        return move_lines

    def _message(self, obj, company):
        company_pool = self.pool['res.company']
        message = company_pool.browse(self.cr, self.uid, company.id, {
                                      'lang': obj.lang}).open_invoices_msg
        return message.split('\n')


class report_open_invoices(models.AbstractModel):
    _name = 'report.partner_report_open_invoices.report_open_invoices'
    _inherit = 'report.abstract_report'
    _template = 'partner_report_open_invoices.report_open_invoices'
    _wrapped_report_class = report_open_invoices_parser
