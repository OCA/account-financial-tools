# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
#   Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.financial.tests.financial_test_classes import \
    FinancialTestCase


class ManualFinancialInstallmentProcess(FinancialTestCase):

    def setUp(self):

        super(ManualFinancialInstallmentProcess, self).setUp()
        # Models
        self.financial_installment = self.env['financial.installment']
        self.financial_installment_simulation = \
            self.env['financial.installment.simulation']

        # Data
        self.main_company = self.env.ref('base.main_company')
        self.main_company.cron_update_reference_date_today()
        self.partner_agrolait_id = self.env.ref('base.res_partner_2')
        self.payment_term_id = \
            self.env.ref('account.account_payment_term_advance')
        self.document_type_id = \
            self.env.ref('financial.DOCUMENTO_FINANCEIRO_CARTAO')
        self.account_rcv_id = \
            self.env.ref('financial.financial_account_101001')

    def create_installment(self):
        """
        Create a draft installment
        :return:  financial.installment
        """
        financial_installment = self.financial_installment.create({
            'document_type_id': self.document_type_id.id,
            'document_number': '100/1',
            'date_document': '2017-01-01',
            'partner_id': self.partner_agrolait_id.id,
            'account_id': self.account_rcv_id.id,
            'amount_document': 100,
            'payment_term_id': self.payment_term_id.id,
            'type': '2pay',
            'company_id': self.main_company.id,
        })
        simulations_dict = financial_installment._onchange_payment_term_id()
        for simulation in simulations_dict:
            self.financial_installment_simulation.create(simulation)
        return financial_installment

    def test_01_check_return_views(self):
        """Scenario 1: create installment"""
        financial_installment = self.create_installment()
        self.assertTrue(financial_installment)
        self.assertEqual(financial_installment.state, 'draft')

    def test_02_confirm_installment(self):
        """Scenario 2: Confirm installment"""
        financial_installment = self.create_installment()
        financial_installment.confirm()
        self.assertEqual(financial_installment.state, 'confirmed')
