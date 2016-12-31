# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import datetime
from openerp import workflow
from openerp.tests import common


class TestPartnerReportOpenInvoices(common.TransactionCase):

    def setUp(self):
        super(TestPartnerReportOpenInvoices, self).setUp()
        self.year = datetime.now().year
        # Create a partner which is supplier as well as customer
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'customer': True,
            'supplier': True
        })

    def test_customer_open_invoice(self):
        self.account_receivable = self.env['account.account'].search(
            [('type', '=', 'receivable'), ('currency_id', '=', False)],
            limit=1)[0]
        # Create customer invoice
        self.customer_invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.account_receivable.id,
            'date_invoice': '%s-01-01' % self.year,
            'type': 'out_invoice',
            'origin': 'TEST-Customer-Inv',
            'invoice_line': [(0, 0, {
                'name': 'Test',
                'account_id': self.account_receivable.id,
                'price_unit': 234.56,
                'quantity': 3,
            })],
        })

        # Change the state of customer invoice from draft to open
        workflow.trg_validate(
            self.uid, 'account.invoice', self.customer_invoice.id,
            'invoice_open', self.cr)
        self.move_line_amount = 0.00
        # Get move line amount of customer invoice
        for move_line_data in self.customer_invoice.move_id.line_id:
            if move_line_data.date_maturity:
                self.move_line_amount += move_line_data.debit
        # Check move line amount and customer invoice amount is same
        self.assertEquals(self.customer_invoice.amount_total,
                          self.move_line_amount)

    def test_supplier_open_invoice(self):
        self.account_payable = self.env['account.account'].search(
            [('type', '=', 'payable'), ('currency_id', '=', False)],
            limit=1)[0]
        # Create supplier invoice
        self.supplier_invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.account_payable.id,
            'date_invoice': '%s-01-01' % self.year,
            'type': 'in_invoice',
            'origin': 'TEST-Supplier-Inv',
            'invoice_line': [(0, 0, {
                'name': 'Test',
                'account_id': self.account_payable.id,
                'price_unit': 789.48,
                'quantity': 2,
            })],
        })
        # Change the state of supplier invoice from draft to open
        workflow.trg_validate(
            self.uid, 'account.invoice', self.supplier_invoice.id,
            'invoice_open', self.cr)
        self.move_line_amount = 0.00
        # Get move line amount of supplier invoice
        for move_line_data in self.supplier_invoice.move_id.line_id:
            if move_line_data.date_maturity:
                self.move_line_amount += move_line_data.credit
        # Check move line amount and supplier invoice amount is same
        self.assertEquals(self.supplier_invoice.amount_total,
                          self.move_line_amount)
