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


class testOnChange(common.TransactionCase):

    def setUp(self):
        super(testOnChange, self).setUp()
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

    def test_balanced_exchanges_gain_loss(self):
        # The point of this test is to show that we handle correctly the gain/loss exchanges during reconciliations in foreign currencies.
        # For instance, with a company set in EUR, and a USD rate set to 0.033,
        # the reconciliation of an invoice of 2.00 USD (60.61 EUR) and a bank statement of two lines of 1.00 USD (30.30 EUR)
        # will lead to an exchange loss, that should be handled correctly within the journal items.
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
        # We create a bank statement with two lines of 1.00 USD each.
        bank_stmt_id = self.acc_bank_stmt_model.create(cr, uid, {
            'journal_id': self.bank_journal_usd_id,
            'date': time.strftime('%Y-%m-%d'),
            'line_ids': [
                (0, 0, {
                    'name': 'half payment',
                    'partner_id': self.partner_agrolait_id,
#                    'amount': 2.0,
                    'amount': 1.0,
                    'date': time.strftime('%Y-%m-%d')
                }),
#                (0, 0, {
#                    'name': 'second half payment',
#                    'partner_id': self.partner_agrolait_id,
#                    'amount': 1.0,
#                    'date': time.strftime('%Y-%m-%d')
#                })
            ]
        })

        statement = self.acc_bank_stmt_model.browse(cr, uid, bank_stmt_id)

        # We process the reconciliation of the invoice line with the two bank statement lines
        line_id = None
        for l in invoice.move_id.line_id:
            if l.account_id.id == self.account_rcv_id:
                line_id = l
                break

        for statement_line in statement.line_ids:
            self.acc_bank_stmt_line_model.process_reconciliation(cr, uid, statement_line.id, [
                {'counterpart_move_line_id': line_id.id, 'credit': 1.0, 'debit': 0.0, 'name': line_id.name}
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
        exchange_loss_line = None
        for line in reconcile.line_id:
            res_account = result.setdefault(line.account_id, {'debit': 0.0, 'credit': 0.0, 'count': 0})
            res_account['debit'] = res_account['debit'] + line.debit
            res_account['credit'] = res_account['credit'] + line.credit
            res_account['count'] += 1
            if line.credit == 0.01:
                exchange_loss_line = line
        # We should be able to find a move line of 0.01 EUR on the Debtors account, being the cent we lost during the currency exchange
        self.assertTrue(exchange_loss_line, 'There should be one move line of 0.01 EUR in credit')
        # The journal items of the reconciliation should have their debit and credit total equal
        # Besides, the total debit and total credit should be 60.61 EUR (2.00 USD)
        self.assertEquals(sum([res['debit'] for res in result.values()]), 60.61)
        self.assertEquals(sum([res['credit'] for res in result.values()]), 60.61)
        counterpart_exchange_loss_line = None
        for line in exchange_loss_line.move_id.line_id:
            if line.account_id.id == self.account_fx_expense_id:
                counterpart_exchange_loss_line = line
        #  We should be able to find a move line of 0.01 EUR on the Foreign Exchange Loss account
        self.assertTrue(counterpart_exchange_loss_line, 'There should be one move line of 0.01 EUR on account "Foreign Exchange Loss"')
