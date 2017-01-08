# -*- coding: utf-8 -*-

from openerp.addons.account_reconcile_trace.tests.common \
    import TestCommon
from openerp.tools import mute_logger
import time


class TestReconcileTrace(TestCommon):

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_00_reconcile_trace(self):
        """ In order to create a Customer Invoice"""

        # I create a invoice line values
        invoice_lines = []

        line_values = {'quantity': 1.0,
                       'price_unit': 75.0,
                       'name': 'test',
                       'product_id': self.product_consultant,
                       'uos_id': self.uom_hour,
                       'account_id': self.sale_account}
        invoice_lines.append((0, 0, line_values))
        # I create a invoice using invoice line data and invoice values
        invoice_values = {
            'partner_id': self.main_customer,
            'account_id': self.receive_account,
            'journal_id': self.sales_journal,
            'date_invoice': time.strftime('%Y-%m-%d'),
            'invoice_line': invoice_lines,
            'type': 'out_invoice',
            'company_id': self.main_company
        }
        self.invoice = self.InvoiceObj.create(invoice_values)
        # I check if the invoice was created
        self.assertTrue(self.invoice, "Invoice no created")
        # I active the invoice workflow to validate the invoice and
        # create the account move associate to this invoice
        self.invoice.signal_workflow('invoice_open')

        # In order to create a Account move to reconcile the
        # invoice account move

        # I create the first move line values
        move_lines = []

        move_values1 = {'name': 'move line 1',
                        'account_id': self.receive_account,
                        'partner_id': self.main_customer,
                        'credit': 75,
                        'company_id': self.main_company}
        move_lines.append((0, 0, move_values1))
        # I create the second move line values
        move_values2 = {'name': 'move line 2',
                        'account_id': self.debit_account,
                        'debit': 75,
                        'company_id': self.main_company}
        move_lines.append((0, 0, move_values2))

        # I find a period using current date
        period_id = self.PeriodObj.find(time.strftime('%Y-%m-%d'))
        if period_id:
            period_id = period_id[0].id

        # I create a account move using move line data and move values dict
        move_values = {
            'journal_id': self.debit_journal,
            'date': time.strftime('%Y-%m-%d'),
            'period_id': period_id,
            'line_id': move_lines}
        self.move = self.MoveObj.create(move_values)
        # I check if the account move was created
        self.assertTrue(self.move, "Account move no created")

        # I validate the account move
        self.move.button_validate()

        # I check the invoice and move amount
        assert self.invoice.amount_total == self.move.amount, \
            'The amount could be 75.0'

        # In order to reconcile the first Account Moves
        invoice_move_id = self.invoice.move_id
        move_line_to_reconcile = False
        for invoice_move_line in invoice_move_id.line_id:
            for move_line in self.move.line_id:
                if invoice_move_line.account_id == move_line.account_id:
                    move_line_to_reconcile = invoice_move_line
                    move_line_to_reconcile += move_line
        if move_line_to_reconcile:
            move_line_to_reconcile.reconcile(
                type='test',
                writeoff_acc_id=self.receive_account,
                writeoff_period_id=period_id,
                writeoff_journal_id=self.debit_journal)

        # In order to pay and reconcile the Account invoice(second move)
        l1 = {
            'name': "Payment test customer invoice",
            'credit': 75.0,
            'account_id': self.debit_account,
            'partner_id': self.main_customer,
            'company_id': self.main_company,
        }
        l2 = {
            'name': "Payment test customer invoice",
            'debit': 75.0,
            'account_id': self.pay_account_id,
            'partner_id': self.main_customer,
            'company_id': self.main_company,
        }
        self.move2 = self.MoveObj.create({'line_id': [(0, 0, l1), (0, 0, l2)],
                                          'journal_id': self.journal_id,
                                          'period_id': period_id,
                                          'date': time.strftime('%Y-%m-%d')})

        # I check if the account move was created
        self.assertTrue(self.move2, "Account move no created")
        # I validate the account move
        self.move2.button_validate()
        # I check the invoice and move amount
        assert self.move.amount == self.move2.amount, \
            'The amount could be 75.0'
        move_line_to_reconcile = False
        for move_line1 in self.move.line_id:
            for move_line2 in self.move2.line_id:
                if move_line1.account_id == move_line2.account_id:
                    move_line_to_reconcile = move_line1
                    move_line_to_reconcile += move_line2
        if move_line_to_reconcile:
            move_line_to_reconcile.reconcile(
                type='test',
                writeoff_acc_id=self.debit_account,
                writeoff_period_id=period_id,
                writeoff_journal_id=self.journal_id)

        # In order to check the account.reconcile.trace.direct moves
        #  up_move_id = asiento de factura,
        #  down_move_id = asiento de "Checks Transfer Debit"
        trace_direct1 = self.TraceDirectObj.search(
            [('up_move_id', '=', invoice_move_id.id),
             ('down_move_id', '=', self.move.id)])

        assert len(trace_direct1) == 1, \
            'The quantity of registry in TraceDirect is not correct.'

        # In order to check every account.reconcile.trace.direct fields
        assert trace_direct1.super_up_move_id == invoice_move_id, \
            'The super_up_move_id is wrong.'
        assert trace_direct1.super_down_move_id == self.move, \
            'The super_down_move_id is wrong.'
        assert trace_direct1.up_journal_id == invoice_move_id.journal_id, \
            'The up_journal_id is wrong.'
        assert trace_direct1.down_journal_id == self.move.journal_id, \
            'The down_journal_id is wrong.'
        assert trace_direct1.up_amount == invoice_move_id.amount, \
            'The up_amount is wrong.'
        assert trace_direct1.down_amount == self.move.amount, \
            'The down_amount is wrong.'
        assert trace_direct1.up_date == invoice_move_id.date, \
            'The up_date is wrong.'
        assert trace_direct1.down_date == self.move.date, \
            'The down_date is wrong.'
        assert trace_direct1.up_ref == invoice_move_id.ref, \
            'The up_ref is wrong.'
        assert trace_direct1.down_ref == self.move.ref, \
            'The down_ref is wrong.'

        # up_move_id = asiento de "Checks Transfer Debit",
        # down_move_id = asiento de "pago" del asiento anterior.
        trace_direct2 = self.TraceDirectObj.search(
            [('up_move_id', '=', self.move.id),
             ('down_move_id', '=', self.move2.id)])

        assert len(trace_direct2) == 1, \
            'The quantity of registry in TraceDirect is not correct.'

        # In order to check every account.reconcile.trace.direct fields
        assert trace_direct2.super_up_move_id == self.move, \
            'The super_up_move_id is wrong.'
        assert trace_direct2.super_down_move_id == self.move2, \
            'The super_down_move_id is wrong.'
        assert trace_direct2.up_journal_id == self.move.journal_id, \
            'The up_journal_id is wrong.'
        assert trace_direct2.down_journal_id == self.move2.journal_id, \
            'The down_journal_id is wrong.'
        assert trace_direct2.up_amount == self.move.amount, \
            'The up_amount is wrong.'
        assert trace_direct2.down_amount == self.move2.amount, \
            'The down_amount is wrong.'
        assert trace_direct2.up_date == self.move.date, \
            'The up_date is wrong.'
        assert trace_direct2.down_date == self.move2.date, \
            'The down_date is wrong.'
        assert trace_direct2.up_ref == self.move.ref, \
            'The up_ref is wrong.'
        assert trace_direct2.down_ref == self.move2.ref, \
            'The down_ref is wrong.'

        # In order to check the account.reconcile.trace.recursive moves
        #  up_move_id = asiento de factura,
        #  down_move_id = asiento de "Checks Transfer Debit"
        trace_recursive1 = self.TraceRecursiveObj.search(
            [('up_move_id', '=', invoice_move_id.id),
             ('down_move_id', '=', self.move.id)])
        assert len(trace_recursive1) == 1, \
            'The quantity of registry in TraceRecursive is not correct.'

        # In order to check every account.reconcile.trace.recursive fields
        assert trace_recursive1.super_up_move_id == \
            trace_direct1.super_up_move_id, \
            'The super_up_move_id is wrong.'
        assert trace_recursive1.super_down_move_id == \
            trace_direct1.super_down_move_id, \
            'The super_down_move_id is wrong.'
        assert trace_recursive1.up_journal_id == \
            trace_direct1.up_journal_id, \
            'The up_journal_id is wrong.'
        assert trace_recursive1.down_journal_id == \
            trace_recursive1.down_journal_id, \
            'The down_journal_id is wrong.'
        assert trace_recursive1.up_amount == trace_direct1.up_amount, \
            'The up_amount is wrong.'
        assert trace_recursive1.down_amount == trace_recursive1.down_amount, \
            'The down_amount is wrong.'
        assert trace_recursive1.up_date == trace_direct1.up_date, \
            'The up_date is wrong.'
        assert trace_recursive1.down_date == trace_recursive1.down_date, \
            'The down_date is wrong.'
        assert trace_recursive1.up_ref == trace_direct1.up_ref, \
            'The up_ref is wrong.'
        assert trace_recursive1.down_ref == trace_recursive1.down_ref, \
            'The down_ref is wrong.'
        # up_move_id = asiento de "Checks Transfer Debit",
        # down_move_id = asiento de "pago" del asiento anterior.
        trace_recursive2 = self.TraceRecursiveObj.search(
            [('up_move_id', '=', self.move.id),
             ('down_move_id', '=', self.move2.id)])

        assert len(trace_recursive2) == 1, \
            'The quantity of registry in TraceRecursive is not correct.'

        # In order to check every account.reconcile.trace.direct fields
        assert trace_recursive2.super_up_move_id == \
            trace_direct1.super_down_move_id, \
            'The super_up_move_id is wrong.'
        assert trace_recursive2.super_down_move_id == \
            trace_direct2.super_down_move_id, \
            'The super_down_move_id is wrong.'
        assert trace_recursive2.up_journal_id == \
            trace_direct1.down_journal_id, \
            'The up_journal_id is wrong.'
        assert trace_recursive2.down_journal_id == \
            trace_direct2.down_journal_id, \
            'The down_journal_id is wrong.'
        assert trace_recursive2.up_amount == trace_direct1.down_amount, \
            'The up_amount is wrong.'
        assert trace_recursive2.down_amount == trace_direct2.down_amount, \
            'The down_amount is wrong.'
        assert trace_recursive2.up_date == trace_direct1.down_date, \
            'The up_date is wrong.'
        assert trace_recursive2.down_date == trace_direct2.down_date, \
            'The down_date is wrong.'
        assert trace_recursive2.up_ref == trace_direct1.down_ref, \
            'The up_ref is wrong.'
        assert trace_recursive2.down_ref == trace_direct2.down_ref, \
            'The down_ref is wrong.'

#
#         trace_recursive3 = self.TraceRecursiveObj.search([
#                                                           ('up_move_id',
#                                                            '=',
#                                                           invoice_move_id.id),
#                                                           ('down_move_id',
#                                                            '=',
#                                                            self.move2.id)])
#        assert len(trace_recursive3) == 1 , \
#            'The quantity of registry in TraceRecursive is not correct.)
#        """In order to check the trace recursive in invoice"""
#        self.invoice.trace_down_ids
#        self.invoice.trace_up_ids
#        """In order to check the trace recursive in account moves"""
#        self.move.trace_down_ids
#        self.move.trace_up_ids
#
#        self.move2.trace_down_ids
#        self.move2.trace_up_ids

    @mute_logger('openerp.addons.base.ir.ir_model', 'openerp.models')
    def test_01_reconcile_trace(self):
        """ In order to create a Supplier Invoice"""

        # I create a invoice line values
        invoice_lines = []

        line_values = {'quantity': 1.0,
                       'price_unit': 30.0,
                       'name': 'test',
                       'product_id': self.product_consultant,
                       'uos_id': self.uom_hour,
                       'account_id': self.expense_account}
        invoice_lines.append((0, 0, line_values))
        # I create a invoice using invoice line data and invoice values
        invoice_values = {'partner_id': self.main_supplier,
                          'account_id': self.payable_account,
                          'journal_id': self.purchase_journal,
                          'date_invoice': time.strftime('%Y-%m-%d'),
                          'invoice_line': invoice_lines,
                          'type': 'in_invoice',
                          'company_id': self.main_company}
        self.invoice = self.InvoiceObj.create(invoice_values)
        # I check if the invoice was created
        self.assertTrue(self.invoice, "Invoice no created")
        # I active the invoice workflow to validate the invoice and
        # create the account move associate to this invoice
        self.invoice.signal_workflow('invoice_open')

        # In order to create a Account move to reconcile the
        # invoice account move

        # I create the first move line values
        move_lines = []

        move_values1 = {'name': 'move line 1',
                        'account_id': self.payable_account,
                        'partner_id': self.main_supplier,
                        'debit': 30,
                        'company_id': self.main_company}
        move_lines.append((0, 0, move_values1))
        # I create the second move line values
        move_values2 = {'name': 'move line 2',
                        'account_id': self.credit_account,
                        'credit': 30,
                        'company_id': self.main_company}
        move_lines.append((0, 0, move_values2))

        # I find a period using current date
        period_id = self.PeriodObj.find(time.strftime('%Y-%m-%d'))
        if period_id:
            period_id = period_id[0].id
        # I create a account move using move line data and move values dict
        move_values = {'journal_id': self.credit_journal,
                       'date': time.strftime('%Y-%m-%d'),
                       'period_id': period_id,
                       'line_id': move_lines}
        self.move = self.MoveObj.create(move_values)
        # I check if the account move was created
        self.assertTrue(self.move, "Account move no created")
        # I validate the account move
        self.move.button_validate()
        # I check the invoice and move amount
        assert self.invoice.amount_total == self.move.amount, \
            'The amount could be 30.0'

        #  In order to reconcile the Account Moves
        invoice_move_id = self.invoice.move_id
        move_line_to_reconcile = False
        for invoice_move_line in invoice_move_id.line_id:
            for move_line in self.move.line_id:
                if invoice_move_line.account_id == move_line.account_id:
                    move_line_to_reconcile = invoice_move_line
                    move_line_to_reconcile += move_line
        if move_line_to_reconcile:
            move_line_to_reconcile.reconcile(
                type='test',
                writeoff_acc_id=self.payable_account,
                writeoff_period_id=period_id,
                writeoff_journal_id=self.credit_journal)

        #  In order to pay and reconcile the Account invoice
        l1 = {
            'name': "Payment test supplier invoice",
            'debit': 30.0,
            'account_id': self.credit_account,
            'partner_id': self.main_supplier,
            'company_id': self.main_company,
        }
        l2 = {
            'name': "Payment test supplier invoice",
            'credit': 30.0,
            'account_id': self.pay_account_id,
            'partner_id': self.main_supplier,
            'company_id': self.main_company,
        }
        self.move2 = self.MoveObj.create({'line_id': [(0, 0, l1), (0, 0, l2)],
                                          'journal_id': self.journal_id,
                                          'period_id': period_id,
                                          'date': time.strftime('%Y-%m-%d')})
        # I check if the account move was created
        self.assertTrue(self.move2, "Account move no created")
        # I validate the account move
        self.move2.button_validate()
        # I check the invoice and move amount
        assert self.move.amount == self.move2.amount, \
            'The amount could be 30.0'
        move_line_to_reconcile = False
        for move_line1 in self.move.line_id:
            for move_line2 in self.move2.line_id:
                if move_line1.account_id == move_line2.account_id:
                    move_line_to_reconcile = move_line1
                    move_line_to_reconcile += move_line2
        if move_line_to_reconcile:
            move_line_to_reconcile.reconcile(
                type='test',
                writeoff_acc_id=self.credit_account,
                writeoff_period_id=period_id,
                writeoff_journal_id=self.journal_id)

        # In order to check the account.reconcile.trace.direct moves
        #  down_move_id = asiento de factura,
        #  up_move_id = asiento de "Checks Transfer Debit"
        trace_direct1 = self.TraceDirectObj.search(
            [('down_move_id', '=', invoice_move_id.id),
             ('up_move_id', '=', self.move.id)])

        assert len(trace_direct1) == 1, \
            'The quantity of registry in TraceDirect is not correct.'

        # In order to check every account.reconcile.trace.direct fields
        assert trace_direct1.super_up_move_id == self.move, \
            'The super_up_move_id is wrong.'
        assert trace_direct1.super_down_move_id == invoice_move_id, \
            'The super_down_move_id is wrong.'
        assert trace_direct1.up_journal_id == self.move.journal_id, \
            'The up_journal_id is wrong.'
        assert trace_direct1.down_journal_id == invoice_move_id.journal_id, \
            'The down_journal_id is wrong.'
        assert trace_direct1.up_amount == self.move.amount, \
            'The up_amount is wrong.'
        assert trace_direct1.down_amount == invoice_move_id.amount, \
            'The down_amount is wrong.'
        assert trace_direct1.up_date == self.move.date, \
            'The up_date is wrong.'
        assert trace_direct1.down_date == invoice_move_id.date, \
            'The down_date is wrong.'
        assert trace_direct1.up_ref == self.move.ref, \
            'The up_ref is wrong.'
        assert trace_direct1.down_ref == invoice_move_id.ref, \
            'The down_ref is wrong.'

        # down_move_id = asiento de "Checks Transfer Debit",
        # up_move_id = asiento de "pago" del asiento anterior.
        trace_direct2 = self.TraceDirectObj.search(
            [('down_move_id', '=', self.move.id),
             ('up_move_id', '=', self.move2.id)])

        assert len(trace_direct2) == 1, \
            'The quantity of registry TraceDirect is not correct.'

        # In order to check every account.reconcile.trace.direct fields
        assert trace_direct2.super_up_move_id == self.move2, \
            'The super_up_move_id is wrong.'
        assert trace_direct2.super_down_move_id == self.move, \
            'The super_down_move_id is wrong.'
        assert trace_direct2.up_journal_id == self.move2.journal_id, \
            'The up_journal_id is wrong.'
        assert trace_direct2.down_journal_id == self.move.journal_id, \
            'The down_journal_id is wrong.'
        assert trace_direct2.up_amount == self.move2.amount, \
            'The up_amount is wrong.'
        assert trace_direct2.down_amount == self.move.amount, \
            'The down_amount is wrong.'
        assert trace_direct2.up_date == self.move2.date, \
            'The up_date is wrong.'
        assert trace_direct2.down_date == self.move.date, \
            'The down_date is wrong.'
        assert trace_direct2.up_ref == self.move2.ref, \
            'The up_ref is wrong.'
        assert trace_direct2.down_ref == self.move.ref, \
            'The down_ref is wrong.'

        # In order to check the account.reconcile.trace.recursive moves
        #  down_move_id = asiento de factura,
        #  up_move_id = asiento de "Checks Transfer Debit"
        trace_recursive1 = self.TraceRecursiveObj.search(
            [('down_move_id', '=', invoice_move_id.id),
             ('up_move_id', '=', self.move.id)])

        assert len(trace_recursive1) == 1, \
            'The quantity of registry in TraceRecursive is not correct.'

        # In order to check every account.reconcile.trace.recursive fields
        assert trace_recursive1.super_up_move_id == \
            trace_direct1.super_up_move_id, \
            'The super_up_move_id is wrong.'
        assert trace_recursive1.super_down_move_id == \
            trace_direct1.super_down_move_id, \
            'The super_down_move_id is wrong.'
        assert trace_recursive1.up_journal_id == \
            trace_recursive1.up_journal_id, \
            'The up_journal_id is wrong.'
        assert trace_recursive1.down_journal_id == \
            trace_direct1.down_journal_id, \
            'The down_journal_id is wrong.'
        assert trace_recursive1.up_amount == trace_recursive1.up_amount, \
            'The up_amount is wrong.'
        assert trace_recursive1.down_amount == trace_direct1.down_amount, \
            'The down_amount is wrong.'
        assert trace_recursive1.up_date == trace_recursive1.up_date, \
            'The up_date is wrong.'
        assert trace_recursive1.down_date == trace_direct1.down_date, \
            'The down_date is wrong.'
        assert trace_recursive1.up_ref == trace_recursive1.up_ref, \
            'The up_ref is wrong.'
        assert trace_recursive1.down_ref == trace_direct1.down_ref, \
            'The down_ref is wrong.'
        # down_move_id = asiento de "Checks Transfer Debit",
        # up_move_id = asiento de "pago" del asiento anterior.
        trace_recursive2 = self.TraceRecursiveObj.search(
            [('down_move_id', '=', self.move.id),
             ('up_move_id', '=', self.move2.id)])

        assert len(trace_recursive2) == 1, \
            'The quantity of registry in TraceRecursive is not correct.'

        # In order to check every account.reconcile.trace.direct fields
        assert trace_recursive2.super_up_move_id == \
            trace_direct2.super_up_move_id, \
            'The super_up_move_id is wrong.'
        assert trace_recursive2.super_down_move_id == \
            trace_direct1.super_up_move_id, \
            'The super_down_move_id is wrong.'
        assert trace_recursive2.up_journal_id == \
            trace_direct2.up_journal_id, \
            'The up_journal_id is wrong.'
        assert trace_recursive2.down_journal_id == \
            trace_direct1.up_journal_id, \
            'The down_journal_id is wrong.'
        assert trace_recursive2.up_amount == trace_direct2.up_amount, \
            'The up_amount is wrong.'
        assert trace_recursive2.down_amount == trace_direct1.up_amount, \
            'The down_amount is wrong.'
        assert trace_recursive2.up_date == trace_direct2.up_date, \
            'The up_date is wrong.'
        assert trace_recursive2.down_date == trace_direct1.up_date, \
            'The down_date is wrong.'
        assert trace_recursive2.up_ref == trace_direct2.up_ref, \
            'The up_ref is wrong.'
        assert trace_recursive2.down_ref == trace_direct1.up_ref, \
            'The down_ref is wrong.'
#
#         trace_recursive3 = self.TraceRecursiveObj.search(
#                                                          [
#                                                           ('down_move_id',
#                                                            '=',
#                                                            invoice_move_id.id),
#                                                           ('up_move_id',
#                                                            '=',
#                                                            self.move2.id)])
#        assert len(trace_recursive3) == 1 , \
#            'The quantity of registry in this model not is correct.'

#        """In order to check the trace recursive in invoice"""
#        self.invoice.trace_down_ids
#        self.invoice.trace_up_ids
#        """In order to check the trace recursive in account moves"""
#        self.move.trace_down_ids
#        self.move.trace_up_ids
#
#        self.move2.trace_down_ids
#        self.move2.trace_up_ids
