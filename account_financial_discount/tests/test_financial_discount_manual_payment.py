# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from freezegun import freeze_time
from odoo import fields
from odoo.tests.common import Form

from .common import TestAccountFinancialDiscountCommon


@freeze_time("2019-04-01")
class TestAccountFinancialDiscountManualPayment(
    TestAccountFinancialDiscountCommon
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice1 = cls.init_invoice(
            cls.partner,
            'in_invoice',
            payment_term=cls.payment_term,
            invoice_date='2019-04-01',
            invoice_date_due='2019-05-01',
        )
        cls.init_invoice_line(cls.invoice1, 1.0, 1000.0)

        cls.invoice2 = cls.init_invoice(
            cls.partner,
            'in_invoice',
            payment_term=cls.payment_term,
            invoice_date='2019-02-15',
            invoice_date_due='2019-03-15',
        )
        cls.init_invoice_line(cls.invoice2, 1.0, 1000.0)

        cls.invoice3 = cls.init_invoice(
            cls.partner,
            'in_invoice',
            payment_term=cls.payment_thirty_net,
            invoice_date='2019-04-01',
            invoice_date_due='2019-05-01',
        )
        cls.init_invoice_line(cls.invoice3, 1.0, 1000.0)

        cls.client_invoice1 = cls.init_invoice(
            cls.customer,
            'out_invoice',
            payment_term=cls.payment_term,
            invoice_date='2019-04-01',
            invoice_date_due='2019-05-01',
        )
        cls.init_invoice_line(cls.client_invoice1, 1.0, 1000.0)

        cls.client_invoice2 = cls.init_invoice(
            cls.customer,
            'out_invoice',
            payment_term=cls.payment_term,
            invoice_date='2019-02-15',
            invoice_date_due='2019-03-15',
        )
        cls.init_invoice_line(cls.client_invoice2, 1.0, 1000.0)

        cls.client_invoice3 = cls.init_invoice(
            cls.customer,
            'out_invoice',
            payment_term=cls.payment_thirty_net,
            invoice_date='2019-04-01',
            invoice_date_due='2019-05-01',
        )
        cls.init_invoice_line(cls.client_invoice3, 1.0, 1000.0)

        cls.amount_without_discount = 1150.0
        cls.amount_discount = 23.0
        cls.amount_with_discount = 1127.0

    def test_invoice_discount_term_line(self):
        """Test saving of discount on payment term line for vendor bills"""
        invoice = self.init_invoice(
            self.partner, "in_invoice", self.payment_term
        )
        self.init_invoice_line(invoice, 1.0, 1000.0)
        self.assertEqual(invoice.date, fields.Date.to_date("2019-04-01"))
        self.assertFalse(invoice.invoice_date)
        with freeze_time("2019-04-15"):
            invoice.post()
            self.assertEqual(invoice.date, fields.Date.to_date("2019-04-15"))
            self.assertEqual(
                invoice.invoice_date, fields.Date.to_date("2019-04-15")
            )
            self.assertTrue(invoice.has_discount_available)
            term_line = invoice.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type == 'payable'
            )
            self.assertEqual(
                term_line.date_discount, fields.Date.to_date("2019-04-25")
            )
            self.assertEqual(term_line.amount_discount, -self.amount_discount)

    def test_customer_invoice_discount_term_line(self):
        """Test saving of discount on payment term line for customer invoice"""
        invoice = self.init_invoice(
            self.customer, "out_invoice", self.payment_term
        )
        self.init_invoice_line(invoice, 1.0, 1000.0)
        self.assertEqual(invoice.date, fields.Date.to_date("2019-04-01"))
        self.assertFalse(invoice.invoice_date)
        with freeze_time("2019-04-15"):
            invoice.post()
            self.assertEqual(invoice.date, fields.Date.to_date("2019-04-15"))
            self.assertEqual(
                invoice.invoice_date, fields.Date.to_date("2019-04-15")
            )
            self.assertTrue(invoice.has_discount_available)
            term_line = invoice.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type == 'receivable'
            )
            self.assertEqual(
                term_line.date_discount, fields.Date.to_date("2019-04-25")
            )
            self.assertEqual(term_line.amount_discount, self.amount_discount)

    def test_invoice_discount_term_line_multicurrency(self):
        """Test saving of discount on payment term line for multi currency vendor bills"""
        invoice = self.init_invoice(
            self.partner,
            "in_invoice",
            self.payment_term,
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice, 1.0, 1000.0)
        self.assertEqual(invoice.date, fields.Date.to_date("2019-04-01"))
        self.assertFalse(invoice.invoice_date)
        with freeze_time("2019-04-15"):
            invoice.post()
            self.assertEqual(invoice.date, fields.Date.to_date("2019-04-15"))
            self.assertEqual(
                invoice.invoice_date, fields.Date.to_date("2019-04-15")
            )
            self.assertTrue(invoice.has_discount_available)
            term_line = invoice.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type == 'payable'
            )
            self.assertEqual(
                term_line.date_discount, fields.Date.to_date("2019-04-25")
            )
            self.assertEqual(
                term_line.amount_discount,
                -self.eur_currency._convert(
                    self.amount_discount,
                    self.usd_currency,
                    invoice.company_id,
                    invoice.date,
                ),
            )
            self.assertEqual(
                term_line.amount_discount_currency, -self.amount_discount
            )

    def test_customer_invoice_discount_term_line_multicurrency(self):
        """Test saving of discount on payment term line for multi currency customer invoice"""
        invoice = self.init_invoice(
            self.customer,
            "out_invoice",
            self.payment_term,
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice, 1.0, 1000.0)
        self.assertEqual(invoice.date, fields.Date.to_date("2019-04-01"))
        self.assertFalse(invoice.invoice_date)
        with freeze_time("2019-04-15"):
            invoice.post()
            self.assertEqual(invoice.date, fields.Date.to_date("2019-04-15"))
            self.assertEqual(
                invoice.invoice_date, fields.Date.to_date("2019-04-15")
            )
            self.assertTrue(invoice.has_discount_available)
            term_line = invoice.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type == 'receivable'
            )
            self.assertEqual(
                term_line.date_discount, fields.Date.to_date("2019-04-25")
            )
            self.assertEqual(
                term_line.amount_discount,
                self.eur_currency._convert(
                    self.amount_discount,
                    self.usd_currency,
                    invoice.company_id,
                    invoice.date,
                ),
            )
            self.assertEqual(
                term_line.amount_discount_currency, self.amount_discount
            )

    def test_manual_payment_with_discount_available(self):
        """Test register payment for a vendor bill with available discount"""
        self.invoice1.post()
        payment_form = Form(
            self.env['account.payment'].with_context(
                active_model='account.move',
                active_ids=self.invoice1.ids,
                active_id=self.invoice1.id,
            )
        )
        self.assertEqual(payment_form.show_force_financial_discount, False)
        self.assertEqual(payment_form.force_financial_discount, False)
        self.assertEqual(payment_form.amount, self.amount_with_discount)
        self.assertEqual(payment_form.payment_difference_handling, 'reconcile')
        self.assertEqual(
            payment_form.payment_difference, -self.amount_discount
        )
        self.assertEqual(payment_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_form.writeoff_label, 'Financial Discount')
        payment = payment_form.save()
        payment.post()
        self.assertEqual(self.invoice1.invoice_payment_state, 'paid')

    def test_manual_payment_with_discount_late_multicurrency(self):
        """Test register payment for a vendor bill with available discount"""
        invoice = self.init_invoice(
            self.partner,
            "in_invoice",
            self.payment_term,
            invoice_date='2019-02-15',
            invoice_date_due='2019-03-15',
            currency=self.eur_currency,
        )
        self.init_invoice_line(invoice, 1.0, 1000.0)
        invoice.post()
        payment_form = Form(
            self.env['account.payment'].with_context(
                active_model='account.move',
                active_ids=invoice.ids,
                active_id=invoice.id,
            )
        )
        self.assertEqual(payment_form.show_force_financial_discount, True)
        self.assertEqual(payment_form.force_financial_discount, False)
        self.assertEqual(payment_form.currency_id, self.eur_currency)
        self.assertEqual(payment_form.amount, self.amount_without_discount)
        payment_form.force_financial_discount = True
        self.assertEqual(payment_form.amount, self.amount_with_discount)
        self.assertEqual(payment_form.payment_difference_handling, 'reconcile')
        self.assertEqual(
            payment_form.payment_difference, -self.amount_discount
        )
        self.assertEqual(payment_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_form.writeoff_label, 'Financial Discount')
        payment_form.currency_id = self.usd_currency
        self.assertEqual(
            payment_form.amount,
            self.eur_currency._convert(
                self.amount_with_discount,
                self.usd_currency,
                invoice.company_id,
                payment_form.payment_date,
            ),
        )
        self.assertEqual(
            payment_form.payment_difference,
            -self.eur_currency._convert(
                self.amount_discount,
                self.usd_currency,
                invoice.company_id,
                payment_form.payment_date,
            ),
        )
        payment = payment_form.save()
        payment.post()
        self.assertEqual(invoice.invoice_payment_state, 'paid')

    def test_manual_payment_with_discount_late(self):
        """Test register payment for a vendor bill with late discount"""
        self.invoice2.post()
        payment_form = Form(
            self.env['account.payment'].with_context(
                active_model='account.move',
                active_ids=self.invoice2.ids,
                active_id=self.invoice2.id,
            )
        )
        self.assertEqual(payment_form.show_force_financial_discount, True)
        self.assertEqual(payment_form.force_financial_discount, False)
        self.assertEqual(payment_form.amount, self.amount_without_discount)
        payment_form.force_financial_discount = True
        self.assertEqual(payment_form.amount, self.amount_with_discount)
        self.assertEqual(payment_form.payment_difference_handling, 'reconcile')
        self.assertEqual(
            payment_form.payment_difference, -self.amount_discount
        )
        self.assertEqual(payment_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_form.writeoff_label, 'Financial Discount')
        payment = payment_form.save()
        payment.post()
        self.assertEqual(self.invoice2.invoice_payment_state, 'paid')

    def test_manual_payment_with_discount_late_forced(self):
        """Test register payment for a vendor bill with late discount forced"""
        self.invoice2.post()
        self.invoice2.force_financial_discount = True
        payment_form = Form(
            self.env['account.payment'].with_context(
                active_model='account.move',
                active_ids=self.invoice2.ids,
                active_id=self.invoice2.id,
            )
        )
        self.assertEqual(payment_form.show_force_financial_discount, True)
        self.assertEqual(payment_form.force_financial_discount, True)
        self.assertEqual(payment_form.amount, self.amount_with_discount)
        self.assertEqual(payment_form.payment_difference_handling, 'reconcile')
        self.assertEqual(
            payment_form.payment_difference, -self.amount_discount
        )
        self.assertEqual(payment_form.writeoff_account_id, self.write_off_rev)
        self.assertEqual(payment_form.writeoff_label, 'Financial Discount')
        payment = payment_form.save()
        payment.post()
        self.assertEqual(self.invoice2.invoice_payment_state, 'paid')

    def test_manual_payment_without_discount(self):
        """Test register payment for a vendor bill without discount"""
        self.invoice3.post()
        payment_form = Form(
            self.env['account.payment'].with_context(
                active_model='account.move',
                active_ids=self.invoice3.ids,
                active_id=self.invoice3.id,
            )
        )
        self.assertEqual(payment_form.show_force_financial_discount, False)
        self.assertEqual(payment_form.force_financial_discount, False)
        self.assertEqual(payment_form.amount, self.amount_without_discount)
        payment = payment_form.save()
        payment.post()
        self.assertEqual(self.invoice3.invoice_payment_state, 'paid')

    @classmethod
    def _get_payment_lines(cls, invoice):
        """Returns payment lines match with the invoice"""
        # Inspired by account.move._get_reconciled_info_JSON_values
        invoice_term_lines = invoice.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type
            in ('receivable', 'payable')
        )
        invoice_matched_lines = invoice_term_lines.mapped(
            'matched_debit_ids'
        ) | invoice_term_lines.mapped('matched_credit_ids')
        invoice_counterpart_lines = invoice_matched_lines.mapped(
            'debit_move_id'
        ) | invoice_matched_lines.mapped('debit_move_id')
        return invoice_counterpart_lines.filtered(
            lambda line: line not in invoice.line_ids
        )

    def test_register_payment_with_discount_available(self):
        """Test register payment for multiple vendor bills with available discount"""
        invoice4 = self.invoice1.copy()
        self.assertTrue(invoice4.has_discount_available)
        invoices = self.invoice1 | invoice4
        invoices.post()
        payment_wizard_form = Form(
            self.env['account.payment.register'].with_context(
                active_ids=invoices.ids, active_model='account.move'
            )
        )
        self.assertFalse(payment_wizard_form.show_force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.create_payments()
        invoice1_payment_lines = self._get_payment_lines(self.invoice1)
        invoice1_payment = invoice1_payment_lines.mapped('payment_id')
        self.assertEqual(invoice1_payment.amount, self.amount_with_discount)
        self.assertEqual(
            invoice1_payment.payment_difference_handling, 'reconcile'
        )
        self.assertEqual(
            invoice1_payment.payment_difference, -self.amount_discount
        )
        self.assertEqual(
            invoice1_payment.writeoff_account_id, self.write_off_rev
        )
        self.assertEqual(invoice1_payment.writeoff_label, 'Financial Discount')
        self.assertEqual(self.invoice1.invoice_payment_state, 'paid')
        invoice4_payment_lines = self._get_payment_lines(invoice4)
        invoice4_payment = invoice4_payment_lines.mapped('payment_id')
        self.assertEqual(invoice4_payment.amount, self.amount_with_discount)
        self.assertEqual(
            invoice4_payment.payment_difference_handling, 'reconcile'
        )
        self.assertEqual(
            invoice4_payment.payment_difference, -self.amount_discount
        )
        self.assertEqual(
            invoice4_payment.writeoff_account_id, self.write_off_rev
        )
        self.assertEqual(invoice4_payment.writeoff_label, 'Financial Discount')
        self.assertEqual(invoice4.invoice_payment_state, 'paid')

    def test_register_payment_with_discount_available_grouped(self):
        """Test register payment grouped for multiple vendor bills with available discount"""
        invoice4 = self.invoice1.copy()
        self.assertTrue(invoice4.has_discount_available)
        invoices = self.invoice1 | invoice4
        invoices.post()
        payment_wizard_form = Form(
            self.env['account.payment.register'].with_context(
                active_ids=invoices.ids, active_model='account.move'
            )
        )
        self.assertFalse(payment_wizard_form.show_force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard_form.group_payment = True
        payment_wizard = payment_wizard_form.save()
        payment_wizard.create_payments()
        invoice1_payment_lines = self._get_payment_lines(self.invoice1)
        invoice1_payment = invoice1_payment_lines.mapped('payment_id')
        invoice4_payment_lines = self._get_payment_lines(invoice4)
        invoice4_payment = invoice4_payment_lines.mapped('payment_id')
        self.assertEqual(invoice1_payment, invoice4_payment)
        self.assertEqual(invoice1_payment.amount, 2254.0)
        self.assertEqual(
            invoice1_payment.payment_difference_handling, 'reconcile'
        )
        self.assertEqual(invoice1_payment.payment_difference, -46.0)
        self.assertEqual(
            invoice1_payment.writeoff_account_id, self.write_off_rev
        )
        self.assertEqual(invoice1_payment.writeoff_label, 'Financial Discount')

        self.assertEqual(self.invoice1.invoice_payment_state, 'paid')
        self.assertEqual(invoice4.invoice_payment_state, 'paid')

    def test_register_payment_with_discount_late(self):
        """Test register payment for multiple vendor bills with late discount"""
        invoice4 = self.invoice2.copy(
            {'invoice_date': self.invoice2.invoice_date}
        )
        self.assertFalse(invoice4.has_discount_available)
        invoices = self.invoice2 | invoice4
        invoices.post()
        payment_wizard_form = Form(
            self.env['account.payment.register'].with_context(
                active_ids=invoices.ids, active_model='account.move'
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.create_payments()
        invoice2_payment_lines = self._get_payment_lines(self.invoice2)
        invoice2_payment = invoice2_payment_lines.mapped('payment_id')
        self.assertEqual(invoice2_payment.amount, self.amount_without_discount)
        self.assertEqual(invoice2_payment.payment_difference, 0.0)
        self.assertEqual(self.invoice2.invoice_payment_state, 'paid')
        invoice4_payment_lines = self._get_payment_lines(invoice4)
        invoice4_payment = invoice4_payment_lines.mapped('payment_id')
        self.assertEqual(invoice4_payment.amount, self.amount_without_discount)
        self.assertEqual(invoice4_payment.payment_difference, 0.0)
        self.assertEqual(invoice4.invoice_payment_state, 'paid')

    def test_register_payment_with_discount_late_forced(self):
        """Test register payment for multiple vendor bills with late discount forced at invoice level"""
        invoice4 = self.invoice2.copy(
            {'invoice_date': self.invoice2.invoice_date}
        )
        self.assertFalse(invoice4.has_discount_available)
        invoice4.force_financial_discount = True
        self.assertTrue(invoice4.has_discount_available)
        invoices = self.invoice2 | invoice4
        invoices.post()
        payment_wizard_form = Form(
            self.env['account.payment.register'].with_context(
                active_ids=invoices.ids, active_model='account.move'
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.create_payments()
        invoice2_payment_lines = self._get_payment_lines(self.invoice2)
        invoice2_payment = invoice2_payment_lines.mapped('payment_id')
        self.assertEqual(invoice2_payment.amount, self.amount_without_discount)
        self.assertEqual(invoice2_payment.payment_difference, 0.0)
        self.assertEqual(self.invoice2.invoice_payment_state, 'paid')
        invoice4_payment_lines = self._get_payment_lines(invoice4)
        invoice4_payment = invoice4_payment_lines.mapped('payment_id')
        self.assertEqual(invoice4_payment.amount, self.amount_with_discount)
        self.assertEqual(
            invoice4_payment.payment_difference_handling, 'reconcile'
        )
        self.assertEqual(
            invoice4_payment.payment_difference, -self.amount_discount
        )
        self.assertEqual(
            invoice4_payment.writeoff_account_id, self.write_off_rev
        )
        self.assertEqual(invoice4_payment.writeoff_label, 'Financial Discount')
        self.assertEqual(invoice4.invoice_payment_state, 'paid')

    def test_register_payment_with_discount_late_forced_wizard(self):
        """Test register payment grouped for multiple vendor bills with late discount forced at wizard level"""
        invoice4 = self.invoice2.copy(
            {'invoice_date': self.invoice2.invoice_date}
        )
        self.assertFalse(invoice4.has_discount_available)
        invoice4.force_financial_discount = True
        self.assertTrue(invoice4.has_discount_available)
        invoices = self.invoice2 | invoice4
        invoices.post()
        payment_wizard_form = Form(
            self.env['account.payment.register'].with_context(
                active_ids=invoices.ids, active_model='account.move'
            )
        )
        self.assertTrue(payment_wizard_form.show_force_financial_discount)
        self.assertFalse(payment_wizard_form.force_financial_discount)
        payment_wizard_form.force_financial_discount = True
        self.assertEqual(
            payment_wizard_form.payment_method_id,
            self.payment_method_manual_out,
        )
        self.assertEqual(payment_wizard_form.journal_id, self.bank_journal)
        payment_wizard = payment_wizard_form.save()
        payment_wizard.create_payments()
        invoice2_payment_lines = self._get_payment_lines(self.invoice2)
        invoice2_payment = invoice2_payment_lines.mapped('payment_id')
        self.assertEqual(invoice2_payment.amount, self.amount_with_discount)
        self.assertEqual(
            invoice2_payment.payment_difference_handling, 'reconcile'
        )
        self.assertEqual(
            invoice2_payment.payment_difference, -self.amount_discount
        )
        self.assertEqual(
            invoice2_payment.writeoff_account_id, self.write_off_rev
        )
        self.assertEqual(invoice2_payment.writeoff_label, 'Financial Discount')
        self.assertEqual(self.invoice2.invoice_payment_state, 'paid')
        invoice4_payment_lines = self._get_payment_lines(invoice4)
        invoice4_payment = invoice4_payment_lines.mapped('payment_id')
        self.assertEqual(invoice4_payment.amount, self.amount_with_discount)
        self.assertEqual(
            invoice4_payment.payment_difference_handling, 'reconcile'
        )
        self.assertEqual(
            invoice4_payment.payment_difference, -self.amount_discount
        )
        self.assertEqual(
            invoice4_payment.writeoff_account_id, self.write_off_rev
        )
        self.assertEqual(invoice4_payment.writeoff_label, 'Financial Discount')
        self.assertEqual(invoice4.invoice_payment_state, 'paid')

    def test_customer_manual_payment_with_discount_available(self):
        """Test register payment for a customer invoice with available discount"""
        self.client_invoice1.post()
        payment_form = Form(
            self.env['account.payment'].with_context(
                active_model='account.move',
                active_ids=self.client_invoice1.ids,
                active_id=self.client_invoice1.id,
            )
        )
        self.assertEqual(payment_form.show_force_financial_discount, False)
        self.assertEqual(payment_form.force_financial_discount, False)
        self.assertEqual(payment_form.amount, self.amount_with_discount)
        self.assertEqual(payment_form.payment_difference_handling, 'reconcile')
        self.assertEqual(payment_form.payment_difference, self.amount_discount)
        self.assertEqual(payment_form.writeoff_account_id, self.write_off_exp)
        self.assertEqual(payment_form.writeoff_label, 'Financial Discount')
        payment = payment_form.save()
        payment.post()
        self.assertEqual(self.client_invoice1.invoice_payment_state, 'paid')

    def test_customer_manual_payment_with_discount_late(self):
        """Test register payment for a customer invoice with late discount"""
        self.client_invoice2.post()
        payment_form = Form(
            self.env['account.payment'].with_context(
                active_model='account.move',
                active_ids=self.client_invoice2.ids,
                active_id=self.client_invoice2.id,
            )
        )
        self.assertEqual(payment_form.show_force_financial_discount, True)
        self.assertEqual(payment_form.force_financial_discount, False)
        self.assertEqual(payment_form.amount, self.amount_without_discount)
        payment_form.force_financial_discount = True
        self.assertEqual(payment_form.amount, self.amount_with_discount)
        self.assertEqual(payment_form.payment_difference_handling, 'reconcile')
        self.assertEqual(payment_form.payment_difference, self.amount_discount)
        self.assertEqual(payment_form.writeoff_account_id, self.write_off_exp)
        self.assertEqual(payment_form.writeoff_label, 'Financial Discount')
        payment = payment_form.save()
        payment.post()
        self.assertEqual(self.client_invoice2.invoice_payment_state, 'paid')

    def test_customer_manual_payment_with_discount_late_forced(self):
        """Test register payment for a customer invoice with late discount forced"""
        self.client_invoice2.post()
        self.client_invoice2.force_financial_discount = True
        payment_form = Form(
            self.env['account.payment'].with_context(
                active_model='account.move',
                active_ids=self.client_invoice2.ids,
                active_id=self.client_invoice2.id,
            )
        )
        self.assertEqual(payment_form.show_force_financial_discount, True)
        self.assertEqual(payment_form.force_financial_discount, True)
        self.assertEqual(payment_form.amount, self.amount_with_discount)
        self.assertEqual(payment_form.payment_difference_handling, 'reconcile')
        self.assertEqual(payment_form.payment_difference, self.amount_discount)
        self.assertEqual(payment_form.writeoff_account_id, self.write_off_exp)
        self.assertEqual(payment_form.writeoff_label, 'Financial Discount')
        payment = payment_form.save()
        payment.post()
        self.assertEqual(self.client_invoice2.invoice_payment_state, 'paid')

    def test_customer_manual_payment_without_discount(self):
        """Test register payment for a customer invoice without discount"""
        self.client_invoice3.post()
        payment_form = Form(
            self.env['account.payment'].with_context(
                active_model='account.move',
                active_ids=self.client_invoice3.ids,
                active_id=self.client_invoice3.id,
            )
        )
        self.assertEqual(payment_form.show_force_financial_discount, False)
        self.assertEqual(payment_form.force_financial_discount, False)
        self.assertEqual(payment_form.amount, self.amount_without_discount)
        payment = payment_form.save()
        payment.post()
        self.assertEqual(self.client_invoice3.invoice_payment_state, 'paid')
