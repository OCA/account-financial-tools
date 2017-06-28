# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
#   Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
from datetime import datetime, timedelta


from odoo import fields
from odoo.tests.common import SingleTransactionCase
from odoo.addons.financial.tests.financial_test_classes import \
    FinancialTestCase


class ManualFinancialProcess(FinancialTestCase):
    """ Story: Manual Financial Process

        As a Financial User
        I want to registry a manual receivable
        So that I can get our cash flow"""

    def setUp(self):
        super(ManualFinancialProcess, self).setUp()

        self.resource_calendar = self.env['resource.calendar']
        self.resource_leaves = self.env['resource.calendar.leaves']

        self.nacional_calendar_id = self.resource_calendar.create({
            'name': 'National Calendar',
        })
        self.new_year_01 = self.resource_leaves.create({
            'name': 'New Year',
            'date_from': fields.Datetime.from_string('2017-01-01 00:00:00'),
            'date_to': fields.Datetime.from_string('2017-01-01 23:59:59'),
            'calendar_id': self.nacional_calendar_id.id,
        })

        self.financial_model = self.env['financial.move']

        self.partner_agrolait = self.env.ref("base.res_partner_2")
        self.partner_axelor = self.env.ref("base.res_partner_2")
        self.currency_chf_id = self.env.ref("base.CHF").id
        self.currency_usd_id = self.env.ref("base.USD").id
        self.currency_eur_id = self.env.ref("base.EUR").id
        self.main_company = self.env.ref('base.main_company').id
        self.env.ref('base.main_company').write(
            {'currency_id': self.currency_eur_id}
        )
        self.bank_112358 = self.env.ref('financial.bank_112358_13')

        self.DOCUMENTO_FINANCEIRO_TED = self.env.ref(
            "financial.DOCUMENTO_FINANCEIRO_TED").id
        self.DOCUMENTO_FINANCEIRO_BOLETO = self.env.ref(
            "financial.DOCUMENTO_FINANCEIRO_BOLETO").id
        self.account_receivable = self.env.ref(
            "financial.financial_account_101001")
        self.account_payable = self.env.ref(
            "financial.financial_account_201008")

    def test_financial_receivable_create(self):
        """Scenario 1: Financial receivable of 100.00

        Given a financial receivable
        And the amount document of 100.00
        And the date of the document is 2017-01-01
        And tne maturity date is 2017-01-01
        And the financial account is 'Receitas com Vendas'
        And the Document number is 1000/1

        When the User confirm the financial

        Then the financial should have the state open
        And the amount residual should be 100
        And the financial should not be reconciled
        And the business maturity date should be 2017-01-02"""

        financial_move = self.create_financial(
            type='2receive',
            amount_document=100,
            currency_id=self.currency_eur_id,
            date_document='2017-01-01',
            date_maturity='2017-01-01',
            account_id=self.env.ref("financial.financial_account_101001").id,
            document_number='100/1',
        )

        financial_move.action_confirm()

        self.assertEqual(financial_move.state, 'open')
        self.assertAlmostEquals(
            financial_move.amount_residual, 100.00)
        self.assertFalse(financial_move.reconciled)
        # FIXME: The resource.leaves don't have a pratical method to call know
        # The next business date!
        # self.assertEqual(financial_move.date_business_maturity,
        #  '2017-01-02')

    def test_financial_receivable_full_pay_one(self):
        """Scenario 1: Financial receivable of 100.00

        Given a financial receivable already confirmed of 100.00
        And the amount document of 100.00
        And the date of the document is 2017-01-01
        And tne business maturity date is 2017-01-02
        And the financial account is 'Receitas com Vendas'
        And the Document number is 1000/1

        When the user create one receipt item related to this receivable
        and the receipt item amount is 100.00

        Then the financial receivable should be paid
        And the amount residual should be 0
        And the financial should be reconciled
        And the final balance of the bank account should be increase 100.00
        """
        financial_move = self.create_financial(
            type='2receive',
            amount_document=100,
            currency_id=self.currency_eur_id,
            date_document='2017-01-01',
            date_maturity='2017-01-01',
            account_id=self.env.ref(
                "financial.financial_account_101001").id,
            document_number='100/1',
        )
        financial_move.action_confirm()

        amount_credit_debit = [100]
        final_state = 'paid'
        # TODO: Verificar se o saldo da conta bancária foi modificado

        bank_account_id = self.bank_112358.id
        bank_initial_balance = 0.00

        for debt in amount_credit_debit:
            self.create_manual_debt(
                financial_move,
                bank_account_id,
                debt
            )

        self.assertEqual(financial_move.state, final_state)
        self.assertAlmostEquals(
            financial_move.amount_residual, 0.00)
        self.assertTrue(financial_move.reconciled)

        self.check_bank_account_balance(
            bank_account_id, bank_initial_balance,
            sum(amount_credit_debit))

    def test_financial_receivable_full_pay_multi(self):
        """Scenario 1: Financial receivable of 5000.00

        Given a financial receivable already confirmed of 5000.00
        And the amount document of 100.00
        And the date of the document is 2017-01-01
        And tne business maturity date is 2017-01-02
        And the financial account is 'Receitas com Vendas'
        And the Document number is 1000/1

        When the user create five receipt item related to this receivable
        and each receipt item amount is 1000.00

        Then the financial receivable should be paid
        And the amount residual should be 0
        And the financial should be reconciled
        And the final balance of the bank account should be increase 5000.00
        """
        financial_move = self.create_financial(
            type='2receive',
            amount_document=5000,
            currency_id=self.currency_eur_id,
            date_document='2017-01-01',
            date_maturity='2017-01-01',
            account_id=self.env.ref(
                "financial.financial_account_101001").id,
            document_number='200/1',
        )
        financial_move.action_confirm()

        amount_credit_debit = [1000, 1000, 1000, 1000, 1000]
        final_state = 'paid'
        # TODO: Verificar se o saldo da conta bancária foi modificado

        bank_account_id = self.bank_112358.id
        bank_initial_balance = 0.00

        for debt in amount_credit_debit:
            self.create_manual_debt(
                financial_move,
                bank_account_id,
                debt
            )

        self.assertEqual(financial_move.state, final_state)
        self.assertAlmostEquals(
            financial_move.amount_residual, 0.00)
        self.assertTrue(financial_move.reconciled)

        self.check_bank_account_balance(
            bank_account_id, bank_initial_balance,
            sum(amount_credit_debit))

    def test_financial_receivable_partial_pay_one(self):
        """Scenario 1: Financial receivable of 5000.00

        Given a financial receivable already confirmed of 5000.00
        And the amount document of 5000.00
        And the date of the document is 2017-01-01
        And tne business maturity date is 2017-01-02
        And the financial account is 'Receitas com Vendas'
        And the Document number is 1000/1

        When the user create one receipt item related to this receivable
        and receipt item amount is 4000.00

        Then the financial receivable should be paid
        And the amount residual should be 1000
        And the financial should be not reconciled
        And the final balance of the bank account should be increase 4000.00
        """
        financial_move = self.create_financial(
            type='2receive',
            amount_document=5000,
            currency_id=self.currency_eur_id,
            date_document='2017-01-01',
            date_maturity='2017-01-01',
            account_id=self.env.ref(
                "financial.financial_account_101001").id,
            document_number='200/1',
        )
        financial_move.action_confirm()

        amount_credit_debit = [4000]
        final_state = 'open'
        # TODO: Verificar se o saldo da conta bancária foi modificado

        bank_account_id = self.bank_112358.id
        bank_initial_balance = 0.00

        for debt in amount_credit_debit:
            self.create_manual_debt(
                financial_move,
                bank_account_id,
                debt
            )

        self.assertEqual(financial_move.state, final_state)
        self.assertAlmostEquals(
            financial_move.amount_residual, 1000.00)
        self.assertFalse(financial_move.reconciled)

        self.check_bank_account_balance(
            bank_account_id, bank_initial_balance,
            sum(amount_credit_debit))

    def test_financial_receivable_partial_pay_multi(self):
        """Scenario 1: Financial receivable of 5000.00

        Given a financial receivable already confirmed of 5000.00
        And the amount document of 100.00
        And the date of the document is 2017-01-01
        And tne business maturity date is 2017-01-02
        And the financial account is 'Receitas com Vendas'
        And the Document number is 1000/1

        When the user create five receipt item related to this receivable
        and each receipt item amount is 1000.00

        Then the financial receivable should be paid
        And the amount residual should be 0
        And the financial should be reconciled
        And the final balance of the bank account should be increase 5000.00
        """
        financial_move = self.create_financial(
            type='2receive',
            amount_document=5000,
            currency_id=self.currency_eur_id,
            date_document='2017-01-01',
            date_maturity='2017-01-01',
            account_id=self.env.ref(
                "financial.financial_account_101001").id,
            document_number='200/1',
        )
        financial_move.action_confirm()

        amount_credit_debit = [1000, 1000, 1000, 1000]
        final_state = 'open'
        # TODO: Verificar se o saldo da conta bancária foi modificado

        bank_account_id = self.bank_112358.id
        bank_initial_balance = 0.00

        for debt in amount_credit_debit:
            self.create_manual_debt(
                financial_move,
                bank_account_id,
                debt
            )

        self.assertEqual(financial_move.state, final_state)
        self.assertAlmostEquals(
            financial_move.amount_residual, 1000.00)
        self.assertFalse(financial_move.reconciled)

        self.check_bank_account_balance(
            bank_account_id, bank_initial_balance,
            sum(amount_credit_debit))
