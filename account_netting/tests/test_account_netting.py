# -*- coding: utf-8 -*-
# (c) 2015 Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import openerp.tests.common as common
from openerp import workflow


class TestAccountNetting(common.TransactionCase):

    def setUp(self):
        super(TestAccountNetting, self).setUp()
        self.partner = self.env['res.partner'].create(
            {'supplier': True,
             'customer': True,
             'name': "Supplier/Customer"
             })
        self.invoice_model = self.env['account.invoice']
        self.account_receivable = self.env.ref('account.a_recv')
        self.customer_invoice = self.invoice_model.create(
            {'journal_id': self.env.ref('account.sales_journal').id,
             'type': 'out_invoice',
             'partner_id': self.partner.id,
             'account_id': self.account_receivable.id,
             'invoice_line': [(0, 0, {'name': 'Test',
                                      'price_unit': 100.0})],
             })
        workflow.trg_validate(
            self.uid, 'account.invoice', self.customer_invoice.id,
            'invoice_open', self.cr)
        customer_move = self.customer_invoice.move_id
        self.move_line_1 = customer_move.line_id.filtered(
            lambda x: x.account_id == self.account_receivable)
        self.account_payable = self.env.ref('account.a_pay')
        self.supplier_invoice = self.invoice_model.create(
            {'journal_id': self.env.ref('account.expenses_journal').id,
             'type': 'in_invoice',
             'partner_id': self.partner.id,
             'account_id': self.account_payable.id,
             'invoice_line': [(0, 0, {'name': 'Test',
                                      'price_unit': 1200.0})],
             })
        workflow.trg_validate(
            self.uid, 'account.invoice', self.supplier_invoice.id,
            'invoice_open', self.cr)
        supplier_move = self.supplier_invoice.move_id
        self.move_line_2 = supplier_move.line_id.filtered(
            lambda x: x.account_id == self.account_payable)

    def test_compensation(self):
        obj = self.env['account.move.make.netting'].with_context(
            active_ids=[self.move_line_1.id, self.move_line_2.id])
        wizard = obj.create(
            {'move_lines': [(6, 0, [self.move_line_1.id,
                                    self.move_line_2.id])],
             'journal': self.env.ref('account.miscellaneous_journal').id})
        res = wizard.button_compensate()
        move = self.env['account.move'].browse(res['res_id'])
        self.assertEqual(
            len(move.line_id), 2,
            'AR/AP netting move has an incorrect line number')
        move_line_receivable = move.line_id.filtered(
            lambda x: x.account_id == self.account_receivable)
        self.assertEqual(
            move_line_receivable.credit, 100,
            'Incorrect credit amount for receivable move line')
        self.assertTrue(
            move_line_receivable.reconcile_id,
            'Receivable move line should be totally reconciled')
        move_line_payable = move.line_id.filtered(
            lambda x: x.account_id == self.account_payable)
        self.assertEqual(
            move_line_payable.debit, 100,
            'Incorrect debit amount for payable move line')
        self.assertTrue(
            move_line_payable.reconcile_partial_id,
            'Receivable move line should be partially reconciled')
