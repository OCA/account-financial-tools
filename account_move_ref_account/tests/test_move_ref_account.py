# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import fields
from odoo.tests.common import SavepointCase


class TestMoveRefAccount(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestMoveRefAccount, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test'})
        cls.account_type_receivable = cls.env['account.account.type'].create({
            'name': 'Test Receivable',
            'type': 'receivable',
        })
        cls.account_type_regular = cls.env['account.account.type'].create({
            'name': 'Test Regular',
            'type': 'other',
        })
        cls.account_receivable = cls.env['account.account'].create({
            'name': 'Test Receivable',
            'code': 'TEST_AR',
            'user_type_id': cls.account_type_receivable.id,
            'reconcile': True,
        })
        cls.account_income = cls.env['account.account'].create({
            'name': 'Test Income',
            'code': 'TEST_IN',
            'user_type_id': cls.account_type_regular.id,
            'reconcile': False,
        })
        cls.sale_journal = \
            cls.env['account.journal'].search([('type', '=', 'sale')])[0]
        cls.journal_bank = \
            cls.env['account.journal'].search([('type', '=', 'bank')])[0]
        cls.payment_method_manual_out = \
            cls.env.ref('account.account_payment_method_manual_in')
        cls.invoice = cls.env['account.invoice'].create({
            'name': "Test Customer Invoice",
            'journal_id': cls.sale_journal.id,
            'partner_id': cls.partner.id,
            'account_id': cls.account_receivable.id,
        })
        cls.invoice_line = cls.env['account.invoice.line']
        cls.invoice_line1 = cls.invoice_line.create({
            'invoice_id': cls.invoice.id,
            'name': 'Line 1',
            'price_unit': 200.0,
            'account_id': cls.account_income.id,
            'quantity': 1,
        })

    def test_01_invoice_payment(self):
        """ Test validate and register payment, following result is expected
        - Journal entry of invoice can link back to invoice
        - Journal entry of payment can link back to payment
        """
        # Open invoice
        self.invoice.action_invoice_open()
        self.assertEqual(self.invoice.move_id.document_id, self.invoice,
                         'Document ID not equal to its invoice')
        self.assertEqual(self.invoice.move_id.document_ref,
                         self.invoice.display_name,
                         'Document Ref not equal to its invoice')
        # Payment
        payment = self.env['account.payment'].create({
            'payment_date': fields.Date.today(),
            'payment_type': 'inbound',
            'amount': 200.00,
            'journal_id': self.journal_bank.id,
            'partner_type': 'customer',
            'partner_id': self.partner.id,
            'payment_method_id': self.payment_method_manual_out.id,
            'invoice_ids': [(4, self.invoice.id, None)],
        })
        payment.post()
        moves = self.env['account.move.line'].search(
            [('payment_id', '=', payment.id)]).mapped('move_id')
        for move in moves:
            self.assertEqual(move.document_id, payment,
                             'Document ID not equal to its payment')
            self.assertEqual(move.document_ref, payment.display_name,
                             'Document Ref not equal to its payment')
