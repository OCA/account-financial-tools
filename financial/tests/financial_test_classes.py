# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time

from odoo.tests.common import SingleTransactionCase


class FinancialTestCase(SingleTransactionCase):
    """ This class extends the base TransactionCase, in order to test the
    financial with localization setups. It is configured to run the tests
    after the installation of all modules, and will SKIP TESTS ifit cannot
    find an already configured accounting (which means no localization
    module has been installed).
    """

    post_install = True
    at_install = False

    def setUp(self):
        super(FinancialTestCase, self).setUp()
        if not self.env['financial.account'].search_count([]):
            self.skipTest("No Financial Chart found")

    def create_financial(self, amount_document=100, type='2receive',
                         currency_id=None, document_number='0000',
                         date_document=False,
                         account_id=False, date_maturity=False):
        """ Returns an open invoice """
        if not date_document:
            date_document = datetime.now()
        if not date_maturity:
            date_maturity = (
                datetime.now() + timedelta(days=30)
            ).strftime('%Y-%m-%d')
        if not account_id:
            if type == '2receive':
                account_id = self.account_receivable.id
            else:
                account_id = self.account_payable.id

        financial = self.financial_model.create({
            'partner_id': self.partner_agrolait.id,
            'currency_id': currency_id,
            'type': type,
            'date_document': date_document,
            'document_type_id': self.DOCUMENTO_FINANCEIRO_TED,
            'document_number': document_number,
            'company_id': self.main_company,
            'account_id': account_id,
            'amount_document': amount_document,
            'date_maturity': date_maturity,
        })
        return financial

    def create_manual_debt(self, financial, bank_account_id, amount_payment):

        # {'active_model': 'financial.move', 'active_ids': [financial.id]}

        ctx = {
            'default_type': financial.type == '2receive' and 'receipt_item' or
            'payment_item',
            'default_amount_document': financial.amount_residual,
            'default_account_id': financial.account_id,
            'default_currency_id': financial.currency_id,
        }

        debt = self.financial_model.with_context(ctx).create({
            'date_payment': datetime.now(),
            'amount_document': amount_payment,
            'document_type_id': self.DOCUMENTO_FINANCEIRO_BOLETO,
            'bank_id': bank_account_id,
            'document_number': financial.document_number,
            'date_credit_debit': (
                datetime.now() + timedelta(days=30)
            ).strftime('%Y-%m-%d'),
            'debt_id': financial.id,
            # 'amount_discount'
            # 'amount_interest'
            # 'amount_paid'
        })

    def check_bank_account_balance(
            self, bank_account, initial_balance, amount_credit_debit):

        return True
