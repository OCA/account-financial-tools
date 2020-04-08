# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import time
from odoo.tests.common import SavepointCase, Form
from odoo.exceptions import UserError


class TestPaymentReversal(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestPaymentReversal, cls).setUpClass()
        # Models
        cls.acc_bank_stmt_model = cls.env['account.bank.statement']
        cls.acc_bank_stmt_line_model = cls.env['account.bank.statement.line']
        cls.partner = cls.env['res.partner'].create({'name': 'Test'})
        cls.account_account_type_model = cls.env['account.account.type']
        cls.account_account_model = cls.env['account.account']
        cls.account_journal_model = cls.env['account.journal']
        cls.account_invoice_model = cls.env['account.invoice']
        cls.account_move_line_model = cls.env['account.move.line']
        cls.invoice_line_model = cls.env['account.invoice.line']
        # Records
        cls.account_type_bank = cls.account_account_type_model.create({
            'name': 'Test Bank',
            'type': 'liquidity',
        })
        cls.account_type_receivable = cls.account_account_type_model.create({
            'name': 'Test Receivable',
            'type': 'receivable',
        })
        cls.account_type_regular = cls.account_account_type_model.create({
            'name': 'Test Regular',
            'type': 'other',
        })
        cls.account_bank = cls.account_account_model.create({
            'name': 'Test Bank',
            'code': 'TEST_BANK',
            'user_type_id': cls.account_type_bank.id,
            'reconcile': False,
        })
        cls.account_receivable = cls.account_account_model.create({
            'name': 'Test Receivable',
            'code': 'TEST_AR',
            'user_type_id': cls.account_type_receivable.id,
            'reconcile': True,
        })
        cls.account_income = cls.account_account_model.create({
            'name': 'Test Income',
            'code': 'TEST_IN',
            'user_type_id': cls.account_type_regular.id,
            'reconcile': False,
        })
        cls.account_expense = cls.account_account_model.create({
            'name': 'Test Expense',
            'code': 'TEST_EX',
            'user_type_id': cls.account_type_regular.id,
            'reconcile': False,
        })
        cls.bank_journal = cls.account_journal_model.create({
            'name': 'Test Bank',
            'code': 'TBK',
            'type': 'bank'
        })
        cls.sale_journal = cls.account_journal_model.\
            search([('type', '=', 'sale')])[0]
        cls.invoice = cls.account_invoice_model.create({
            'name': "Test Customer Invoice",
            'journal_id': cls.sale_journal.id,
            'partner_id': cls.partner.id,
            'account_id': cls.account_receivable.id,
        })

        cls.invoice_line1 = cls.invoice_line_model.create({
            'invoice_id': cls.invoice.id,
            'name': 'Line 1',
            'price_unit': 200.0,
            'account_id': cls.account_income.id,
            'quantity': 1,
        })

    def test_payment_cancel_normal(self):
        """ Tests that, if I don't use cancel reversal,
        I can create an invoice, pay it and then cancel as normal. I expect:
        - account move are removed completely
        """
        # Test journal with normal cancel
        self.bank_journal.write({'update_posted': True,
                                 'cancel_method': 'normal'})
        # Open invoice
        self.invoice.action_invoice_open()
        # Pay invoice
        self.invoice.pay_and_reconcile(self.bank_journal, 200.0)
        payment = self.invoice.payment_ids[0]
        payment.cancel()
        move_lines = self.env['account.move.line'].\
            search([('payment_id', '=', payment.id)])
        # All account moves are removed completely
        self.assertFalse(move_lines)

    def test_payment_cancel_reversal(self):
        """ Tests that if I use cancel reversal, I can create an invoice,
        pay it and then cancel the payment. I expect:
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

    def test_bank_statement_cancel_normal(self):
        """ Tests that, if I don't use cancel reversal,
        I can create an invoice, pay it via a bank statement
        line and then cancel the bank statement line as normal. I expect:
        - account move are removed completely
        """
        # Test journal with normal cancel
        self.bank_journal.write({'update_posted': True,
                                 'cancel_method': 'normal'})
        # Open invoice
        self.invoice.action_invoice_open()
        bank_stmt = self.acc_bank_stmt_model.create({
            'journal_id': self.bank_journal.id,
            'date': time.strftime('%Y') + '-07-15',
            'name': 'payment' + self.invoice.name
        })
        bank_stmt_line = self.acc_bank_stmt_line_model.create(
            {'name': 'payment',
             'statement_id': bank_stmt.id,
             'partner_id': self.partner.id,
             'amount': 200,
             'date': time.strftime('%Y') + '-07-15', })
        line_id = self.account_move_line_model
        # reconcile the payment with the invoice
        for l in self.invoice.move_id.line_ids:
            if l.account_id.id == self.account_receivable.id:
                line_id = l
                break
        bank_stmt_line.process_reconciliation(counterpart_aml_dicts=[{
            'move_line': line_id,
            'account_id': self.account_income.id,
            'debit': 0.0,
            'credit': 200.0,
            'name': 'test_reconciliation',
        }])
        self.assertTrue(bank_stmt_line.journal_entry_ids)
        original_move_lines = bank_stmt_line.journal_entry_ids
        self.assertTrue(original_move_lines.mapped('statement_id'))
        # Cancel the statement line
        bank_stmt_line.button_cancel_reconciliation()
        move_lines = self.env['account.move.line'].\
            search([('statement_id', '=', bank_stmt.id)])
        # All account moves are removed completely
        self.assertFalse(move_lines)

    def test_bank_statement_cancel_reversal_01(self):
        """ Tests that I can create an invoice, pay it via a bank statement
        line and then reverse the bank statement line. I expect:
        - Reversal journal entry is created, and reconciled with original entry
        - Payment is deleted
        - The invoice is not reconciled with the payment anymore
        - The line in the statement is ready to reconcile again
        """
        # Test journal
        self.bank_journal.write({'update_posted': True,
                                 'cancel_method': 'reversal'})
        # Open invoice
        self.invoice.action_invoice_open()
        bank_stmt = self.acc_bank_stmt_model.create({
            'journal_id': self.bank_journal.id,
            'date': time.strftime('%Y') + '-07-15',
            'name': 'payment' + self.invoice.name
        })

        bank_stmt_line = self.acc_bank_stmt_line_model.create(
            {'name': 'payment',
             'statement_id': bank_stmt.id,
             'partner_id': self.partner.id,
             'amount': 200,
             'date': time.strftime('%Y') + '-07-15', })
        line_id = self.account_move_line_model
        # reconcile the payment with the invoice
        for l in self.invoice.move_id.line_ids:
            if l.account_id.id == self.account_receivable.id:
                line_id = l
                break
        bank_stmt_line.process_reconciliation(counterpart_aml_dicts=[{
            'move_line': line_id,
            'account_id': self.account_income.id,
            'debit': 0.0,
            'credit': 200.0,
            'name': 'test_reconciliation',
        }])
        self.assertTrue(bank_stmt_line.journal_entry_ids)
        original_move_lines = bank_stmt_line.journal_entry_ids
        original_payment_id = original_move_lines.mapped('payment_id').id
        self.assertTrue(original_move_lines.mapped('statement_id'))
        # Cancel the statement line
        res = bank_stmt_line.button_cancel_reconciliation()
        ctx = {'active_model': 'account.bank.statement.line',
               'active_ids': [bank_stmt_line.id]}
        f = Form(self.env[res['res_model']].with_context(ctx))
        self.assertEqual(res['res_model'], 'reverse.account.document')
        cancel_wizard = f.save()
        cancel_wizard.action_cancel()
        self.assertFalse(bank_stmt_line.journal_entry_ids)
        payment = self.env['account.payment'].search(
            [('id', '=', original_payment_id)],
            limit=1)
        self.assertFalse(payment)
        self.assertFalse(original_move_lines.mapped('statement_id'))
        move = original_move_lines[0].move_id
        reversed_move = move.reverse_entry_id
        move_reconcile = move.mapped('line_ids').mapped('full_reconcile_id')
        reversed_move_reconcile = \
            reversed_move.mapped('line_ids').mapped('full_reconcile_id')
        # Check
        self.assertTrue(move_reconcile)
        self.assertTrue(reversed_move_reconcile)
        self.assertEqual(move_reconcile, reversed_move_reconcile)

    def test_bank_statement_cancel_reversal_02(self):
        """ Tests that I can create a bank statement line and reconcile it
        to an expense account, and then reverse the reconciliation of the
        statement line. I expect:
        - Reversal journal entry is created, and reconciled with original entry
        - Payment is deleted
        - The line in the statement is ready to reconcile again
        """
        # Test journal
        self.bank_journal.write({'update_posted': True,
                                 'cancel_method': 'reversal'})
        # Create a bank statement
        bank_stmt = self.acc_bank_stmt_model.create({
            'journal_id': self.bank_journal.id,
            'date': time.strftime('%Y') + '-07-15',
            'name': 'payment' + self.invoice.name
        })
        bank_stmt_line = self.acc_bank_stmt_line_model.create(
            {'name': 'payment',
             'statement_id': bank_stmt.id,
             'partner_id': self.partner.id,
             'amount': 200,
             'date': time.strftime('%Y') + '-07-15', })
        line_id = self.account_move_line_model

        bank_stmt_line.process_reconciliation(new_aml_dicts=[{
            'move_line': line_id,
            'account_id': self.account_expense.id,
            'debit': 200.0,
            'name': 'test_expense_reconciliation',
        }])
        self.assertTrue(bank_stmt_line.journal_entry_ids)
        original_move_lines = bank_stmt_line.journal_entry_ids
        original_payment_id = original_move_lines.mapped('payment_id').id
        self.assertTrue(original_move_lines.mapped('statement_id'))
        # Cancel the statement line
        res = bank_stmt_line.button_cancel_reconciliation()
        ctx = {'active_model': 'account.bank.statement.line',
               'active_ids': [bank_stmt_line.id]}
        f = Form(self.env[res['res_model']].with_context(ctx))
        self.assertEqual(res['res_model'], 'reverse.account.document')
        cancel_wizard = f.save()
        cancel_wizard.action_cancel()
        self.assertFalse(bank_stmt_line.journal_entry_ids)
        payment = self.env['account.payment'].search(
            [('id', '=', original_payment_id)],
            limit=1)
        self.assertFalse(payment)
        self.assertFalse(original_move_lines.mapped('statement_id'))
        move = original_move_lines[0].move_id
        reversed_move = move.reverse_entry_id
        move_reconcile = move.mapped('line_ids').mapped('full_reconcile_id')
        reversed_move_reconcile = \
            reversed_move.mapped('line_ids').mapped('full_reconcile_id')
        # Check
        self.assertTrue(move_reconcile)
        self.assertTrue(reversed_move_reconcile)
        self.assertEqual(move_reconcile, reversed_move_reconcile)

    def test_bank_statement_cancel_exception(self):
        """ Tests on exception case, if statement is already validated, but
        user cancel statement line. I expect:
        - UserError will show
        """
        # Test journal
        self.bank_journal.write({'update_posted': True,
                                 'cancel_method': 'reversal'})
        # Create a bank statement
        bank_stmt = self.acc_bank_stmt_model.create({
            'journal_id': self.bank_journal.id,
            'date': time.strftime('%Y') + '-07-15',
            'name': 'payment' + self.invoice.name
        })
        bank_stmt_line = self.acc_bank_stmt_line_model.create(
            {'name': 'payment',
             'statement_id': bank_stmt.id,
             'partner_id': self.partner.id,
             'amount': 200,
             'date': time.strftime('%Y') + '-07-15', })
        line_id = self.account_move_line_model

        bank_stmt_line.process_reconciliation(new_aml_dicts=[{
            'move_line': line_id,
            'account_id': self.account_expense.id,
            'debit': 200.0,
            'name': 'test_expense_reconciliation',
        }])

        bank_stmt.balance_end_real = 200.00
        bank_stmt.check_confirm_bank()
        self.assertEqual(bank_stmt.state, 'confirm')
        with self.assertRaises(UserError):
            bank_stmt_line.button_cancel_reconciliation()
