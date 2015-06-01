# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Damien Crier
#    Copyright 2015 Camptocamp SA
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

from datetime import datetime
import time
from openerp.tests import common


class testCounterpart(common.TransactionCase):

    def setUp(self):
        super(testCounterpart, self).setUp()
        self.account_invoice_model = self.registry('account.invoice')
        self.account_invoice_line_model = self.registry('account.invoice.line')
        self.acc_bank_stmt_model = self.registry('account.bank.statement')
        self.acc_bank_stmt_line_model = self.registry('account.bank.statement.line')
        self.res_currency_model = self.registry('res.currency')
        self.res_currency_rate_model = self.registry('res.currency.rate')

        self.partner_agrolait_id = self.registry("ir.model.data").get_object_reference(self.cr, self.uid, "base", "res_partner_2")[1]
        self.currency_swiss_id = self.registry("ir.model.data").get_object_reference(self.cr, self.uid, "base", "CHF")[1]
        self.currency_usd_id = self.registry("ir.model.data").get_object_reference(self.cr, self.uid, "base", "USD")[1]
        self.account_rcv_id = self.registry("ir.model.data").get_object_reference(self.cr, self.uid, "account", "a_recv")[1]
        self.account_fx_income_id = self.registry("ir.model.data").get_object_reference(self.cr, self.uid, "account", "income_fx_income")[1]
        self.account_fx_expense_id = self.registry("ir.model.data").get_object_reference(self.cr, self.uid, "account", "income_fx_expense")[1]

        self.product_id = self.registry("ir.model.data").get_object_reference(self.cr, self.uid, "product", "product_product_4")[1]

        self.bank_journal_usd_id = self.registry("ir.model.data").get_object_reference(self.cr, self.uid, "account", "bank_journal_usd")[1]
        self.account_usd_id = self.registry("ir.model.data").get_object_reference(self.cr, self.uid, "account", "usd_bnk")[1]

    def test_reconcile_1(self):
        # pur match
        cr, uid = self.cr, self.uid
        # We update the currency rate of the currency USD in order to force the gain/loss exchanges in next steps
        self.res_currency_rate_model.create(cr, uid, {
            'name': time.strftime('%Y-%m-%d') + ' 00:00:00',
            'currency_id': self.currency_usd_id,
            'rate': 0.033,
        })
        # We create a customer invoice of 2.00 USD
        invoice_id = self.account_invoice_model.create(cr, uid, {
            'partner_id': self.partner_agrolait_id,
            'currency_id': self.currency_usd_id,
            'name': 'Foreign invoice with exchange gain',
            'account_id': self.account_rcv_id,
            'type': 'out_invoice',
            'date_invoice': time.strftime('%Y-%m-%d'),
            'journal_id': self.bank_journal_usd_id,
            'invoice_line': [
                (0, 0, {
                    'name': 'line that will lead to an exchange gain',
                    'quantity': 1,
                    'price_unit': 2,
                    'account_analytic_id': self.ref('account.analytic_agrolait')
                })
            ]
        })
        self.registry('account.invoice').signal_workflow(cr, uid, [invoice_id], 'invoice_open')
        invoice = self.account_invoice_model.browse(cr, uid, invoice_id)
        bank_stmt_id = self.acc_bank_stmt_model.create(cr, uid, {
            'journal_id': self.bank_journal_usd_id,
            'date': time.strftime('%Y-%m-%d'),
            'line_ids': [
                (0, 0, {
                    'name': 'Payment',
                    'partner_id': self.partner_agrolait_id,
                    'amount': 7.93,
                    'amount_currency': 2.0,
                    'currency_id': self.currency_usd_id,
                    'date': time.strftime('%Y-%m-%d')
                })
            ]
        })

        statement = self.acc_bank_stmt_model.browse(cr, uid, bank_stmt_id)

        # We process the reconciliation of the invoice line
        line_id = None
        for l in invoice.move_id.line_id:
            if l.account_id.id == self.account_rcv_id:
                line_id = l
                break

        for statement_line in statement.line_ids:
            self.acc_bank_stmt_line_model.process_reconciliation(cr, uid, statement_line.id, [
                {'counterpart_move_line_id': line_id.id, 'credit': 2.0, 'debit': 0.0, 'name': line_id.name}
            ])

        # The invoice should be paid, as the payments totally cover its total
        self.assertEquals(invoice.state, 'paid', 'The invoice should be paid by now')
        reconcile = None
        for payment in invoice.payment_ids:
            reconcile = payment.reconcile_id
            break
        # The invoice should be reconciled (entirely, not a partial reconciliation)
        self.assertTrue(reconcile, 'The invoice should be totally reconciled')
        result = {}
        for line in reconcile.line_id:
            res_account = result.setdefault(line.account_id, {'debit': 0.0, 'credit': 0.0, 'count': 0})
            res_account['debit'] = res_account['debit'] + line.debit
            res_account['credit'] = res_account['credit'] + line.credit
            res_account['count'] += 1
        # The journal items of the reconciliation should have their debit and credit total equal
        # Besides, the total debit and total credit should be 60.61 EUR (2.00 USD)
        self.assertEquals(sum([res['debit'] for res in result.values()]), 79.31)
        self.assertEquals(sum([res['credit'] for res in result.values()]), 79.31)

    def test_reconcile_2(self):
        # exchange gain 0.01
        cr, uid = self.cr, self.uid
        # We update the currency rate of the currency USD in order to force the gain/loss exchanges in next steps
        self.res_currency_rate_model.create(cr, uid, {
            'name': time.strftime('%Y-%m-%d') + ' 00:00:00',
            'currency_id': self.currency_usd_id,
            'rate': 0.033,
        })
        # We create a customer invoice of 2.00 USD
        invoice_id = self.account_invoice_model.create(cr, uid, {
            'partner_id': self.partner_agrolait_id,
            'currency_id': self.currency_usd_id,
            'name': 'Foreign invoice with exchange gain',
            'account_id': self.account_rcv_id,
            'type': 'out_invoice',
            'date_invoice': time.strftime('%Y-%m-%d'),
            'journal_id': self.bank_journal_usd_id,
            'invoice_line': [
                (0, 0, {
                    'name': 'line that will lead to an exchange gain',
                    'quantity': 1,
                    'price_unit': 2,
                    'account_analytic_id':self.ref('account.analytic_agrolait')
                })
            ]
        })
        self.registry('account.invoice').signal_workflow(cr, uid, [invoice_id], 'invoice_open')
        invoice = self.account_invoice_model.browse(cr, uid, invoice_id)
        bank_stmt_id = self.acc_bank_stmt_model.create(cr, uid, {
            'journal_id': self.bank_journal_usd_id,
            'date': time.strftime('%Y-%m-%d'),
            'line_ids': [
                (0, 0, {
                    'name': 'Payment',
                    'partner_id': self.partner_agrolait_id,
                    'amount': 7.94,
                    'amount_currency': 2.0,
                    'currency_id': self.currency_usd_id,
                    'date': time.strftime('%Y-%m-%d')
                })
            ]
        })

        statement = self.acc_bank_stmt_model.browse(cr, uid, bank_stmt_id)

        # We process the reconciliation of the invoice line
        line_id = None
        for l in invoice.move_id.line_id:
            if l.account_id.id == self.account_rcv_id:
                line_id = l
                break

        for statement_line in statement.line_ids:
            self.acc_bank_stmt_line_model.process_reconciliation(cr, uid, statement_line.id, [
                {'counterpart_move_line_id': line_id.id, 'credit': 2.0, 'debit': 0.0, 'name': line_id.name}
            ])

        # The invoice should be paid, as the payments totally cover its total
        self.assertEquals(invoice.state, 'paid', 'The invoice should be paid by now')
        reconcile = None
        for payment in invoice.payment_ids:
            reconcile = payment.reconcile_id
            break
        # The invoice should be reconciled (entirely, not a partial reconciliation)
        self.assertTrue(reconcile, 'The invoice should be totally reconciled')
        result = {}
        for line in reconcile.line_id:
            res_account = result.setdefault(line.account_id, {'debit': 0.0, 'credit': 0.0, 'count': 0})
            res_account['debit'] = res_account['debit'] + line.debit
            res_account['credit'] = res_account['credit'] + line.credit
            res_account['count'] += 1
        # The journal items of the reconciliation should have their debit and credit total equal
        # Besides, the total debit and total credit should be 60.61 EUR (2.00 USD)
        self.assertEquals(sum([res['debit'] for res in result.values()]), 79.31)
        self.assertEquals(sum([res['credit'] for res in result.values()]), 79.31)

    def test_reconcile_3(self):
        # exchange loss 0.01
        cr, uid = self.cr, self.uid
        # We update the currency rate of the currency USD in order to force the gain/loss exchanges in next steps
        self.res_currency_rate_model.create(cr, uid, {
            'name': time.strftime('%Y-%m-%d') + ' 00:00:00',
            'currency_id': self.currency_usd_id,
            'rate': 0.033,
        })
        # We create a customer invoice of 2.00 USD
        invoice_id = self.account_invoice_model.create(cr, uid, {
            'partner_id': self.partner_agrolait_id,
            'currency_id': self.currency_usd_id,
            'name': 'Foreign invoice with exchange gain',
            'account_id': self.account_rcv_id,
            'type': 'out_invoice',
            'date_invoice': time.strftime('%Y-%m-%d'),
            'journal_id': self.bank_journal_usd_id,
            'invoice_line': [
                (0, 0, {
                    'name': 'line that will lead to an exchange gain',
                    'quantity': 1,
                    'price_unit': 2,
                    'account_analytic_id': self.ref('account.analytic_agrolait')
                })
            ]
        })
        self.registry('account.invoice').signal_workflow(cr, uid, [invoice_id], 'invoice_open')
        invoice = self.account_invoice_model.browse(cr, uid, invoice_id)
        # We create a bank statement
        bank_stmt_id = self.acc_bank_stmt_model.create(cr, uid, {
            'journal_id': self.bank_journal_usd_id,
            'date': time.strftime('%Y-%m-%d'),
            'line_ids': [
                (0, 0, {
                    'name': 'Payment',
                    'partner_id': self.partner_agrolait_id,
                    'amount': 7.92,
                    'amount_currency': 2.0,
                    'currency_id': self.currency_usd_id,
                    'date': time.strftime('%Y-%m-%d')
                })
            ]
        })

        statement = self.acc_bank_stmt_model.browse(cr, uid, bank_stmt_id)

        # We process the reconciliation of the invoice line
        line_id = None
        for l in invoice.move_id.line_id:
            if l.account_id.id == self.account_rcv_id:
                line_id = l
                break

        for statement_line in statement.line_ids:
            self.acc_bank_stmt_line_model.process_reconciliation(cr, uid, statement_line.id, [
                {'counterpart_move_line_id': line_id.id, 'credit': 2.0, 'debit': 0.0, 'name': line_id.name}
            ])

        # The invoice should be paid, as the payments totally cover its total
        self.assertEquals(invoice.state, 'paid', 'The invoice should be paid by now')
        reconcile = None
        for payment in invoice.payment_ids:
            reconcile = payment.reconcile_id
            break
        # The invoice should be reconciled (entirely, not a partial reconciliation)
        self.assertTrue(reconcile, 'The invoice should be totally reconciled')
        result = {}
        for line in reconcile.line_id:
            res_account = result.setdefault(line.account_id, {'debit': 0.0, 'credit': 0.0, 'count': 0})
            res_account['debit'] = res_account['debit'] + line.debit
            res_account['credit'] = res_account['credit'] + line.credit
            res_account['count'] += 1
        # The journal items of the reconciliation should have their debit and credit total equal
        # Besides, the total debit and total credit should be 79.31 EUR (2.00 USD)
        self.assertEquals(sum([res['debit'] for res in result.values()]), 79.31)
        self.assertEquals(sum([res['credit'] for res in result.values()]), 79.31)

    def test_reconcile_4(self):
        # no currency conversion rate defined
        cr, uid = self.cr, self.uid
        # We update the currency rate of the currency USD in order to force the gain/loss exchanges in next steps
#         self.res_currency_rate_model.create(cr, uid, {
#             'name': time.strftime('%Y-%m-%d') + ' 00:00:00',
#             'currency_id': self.currency_usd_id,
#             'rate': 0.033,
#         })
        # We create a customer invoice of 2.00 USD
        invoice_id = self.account_invoice_model.create(cr, uid, {
            'partner_id': self.partner_agrolait_id,
            'currency_id': self.currency_usd_id,
            'name': 'Foreign invoice with exchange gain',
            'account_id': self.account_rcv_id,
            'type': 'out_invoice',
            'date_invoice': time.strftime('%Y-%m-%d'),
            'journal_id': self.bank_journal_usd_id,
            'invoice_line': [
                (0, 0, {
                    'name': 'line that will lead to an exchange gain',
                    'quantity': 1,
                    'price_unit': 2,
                    'account_analytic_id': self.ref('account.analytic_agrolait')
                })
            ]
        })
        self.registry('account.invoice').signal_workflow(cr, uid, [invoice_id], 'invoice_open')
        invoice = self.account_invoice_model.browse(cr, uid, invoice_id)
        # We create a bank statement
        bank_stmt_id = self.acc_bank_stmt_model.create(cr, uid, {
            'journal_id': self.bank_journal_usd_id,
            'date': time.strftime('%Y-%m-%d'),
            'line_ids': [
                (0, 0, {
                    'name': 'Payment',
                    'partner_id': self.partner_agrolait_id,
                    'amount': 7.93,
                    'amount_currency': 2.0,
                    'currency_id': self.currency_usd_id,
                    'date': time.strftime('%Y-%m-%d')
                })
            ]
        })

        statement = self.acc_bank_stmt_model.browse(cr, uid, bank_stmt_id)

        # We process the reconciliation of the invoice line
        line_id = None
        for l in invoice.move_id.line_id:
            if l.account_id.id == self.account_rcv_id:
                line_id = l
                break

        for statement_line in statement.line_ids:
            self.acc_bank_stmt_line_model.process_reconciliation(cr, uid, statement_line.id, [
                {'counterpart_move_line_id': line_id.id, 'credit': 2.0, 'debit': 0.0, 'name': line_id.name}
            ])

        # The invoice should be paid, as the payments totally cover its total
        self.assertEquals(invoice.state, 'paid', 'The invoice should be paid by now')
        reconcile = None
        for payment in invoice.payment_ids:
            reconcile = payment.reconcile_id
            break
        # The invoice should be reconciled (entirely, not a partial reconciliation)
        self.assertTrue(reconcile, 'The invoice should be totally reconciled')
        result = {}
        for line in reconcile.line_id:
            res_account = result.setdefault(line.account_id, {'debit': 0.0, 'credit': 0.0, 'count': 0})
            res_account['debit'] = res_account['debit'] + line.debit
            res_account['credit'] = res_account['credit'] + line.credit
            res_account['count'] += 1
        # The journal items of the reconciliation should have their debit and credit total equal
        # Besides, the total debit and total credit should be 7.93 EUR (2.00 USD)
        self.assertEquals(round(sum([res['debit'] for res in result.values()]), 2), 7.93)
        self.assertEquals(round(sum([res['credit'] for res in result.values()]), 2), 7.93)
