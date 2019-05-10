# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import SavepointCase, Form


class TestInvoiceReversal(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestInvoiceReversal, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test'})
        cls.account_type_bank = cls.env['account.account.type'].create({
            'name': 'Test Bank',
            'type': 'liquidity',
        })
        cls.account_type_receivable = cls.env['account.account.type'].create({
            'name': 'Test Receivable',
            'type': 'receivable',
        })
        cls.account_type_regular = cls.env['account.account.type'].create({
            'name': 'Test Regular',
            'type': 'other',
        })
        cls.account_bank = cls.env['account.account'].create({
            'name': 'Test Bank',
            'code': 'TEST_BANK',
            'user_type_id': cls.account_type_bank.id,
            'reconcile': False,
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
        cls.bank_journal = cls.env['account.journal'].create({
            'name': 'Test Bank',
            'code': 'TBK',
            'type': 'bank'
        })
        cls.sale_journal = cls.env['account.journal'].\
            search([('type', '=', 'sale')])[0]
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

    def test_payment_cancel(self):
        """ Tests that I can create an invoice, pay it and then cancel
        the payment. I expect:
        - Reversal journal entry is created, and reconciled with original entry
        - Status of the payment is changed to cancel
        - The invoice is not reconciled with the payment anymore
        """
        # Test journal
        self.bank_journal.write({'update_posted': True,
                                 'cancel_method': 'reversal'})
        # Open invoice
        self.invoice.action_invoice_open()
        # Pay invoice
        self.invoice.pay_and_reconcile(self.bank_journal, 200.0)
        payment = self.invoice.payment_ids[0]
        move = self.env['account.move.line'].search(
            [('payment_id', '=', payment.id)], limit=1).move_id
        res = payment.cancel()
        # Cancel payment
        ctx = {'active_model': 'account.payment',
               'active_ids': [payment.id]}
        f = Form(self.env[res['res_model']].with_context(ctx))
        self.assertEqual(res['res_model'], 'reverse.account.document')
        cancel_wizard = f.save()
        cancel_wizard.action_cancel()
        payment_moves = self.env['account.move.line'].search(
            [('payment_id', '=', payment.id)])
        self.assertFalse(payment_moves)
        reversed_move = move.reverse_entry_id
        move_reconcile = move.mapped('line_ids').mapped('full_reconcile_id')
        reversed_move_reconcile = \
            reversed_move.mapped('line_ids').mapped('full_reconcile_id')
        # Check
        self.assertTrue(move_reconcile)
        self.assertTrue(reversed_move_reconcile)
        self.assertEqual(move_reconcile, reversed_move_reconcile)
        self.assertEqual(payment.state, 'cancelled')
        self.assertEqual(self.invoice.state, 'open')
