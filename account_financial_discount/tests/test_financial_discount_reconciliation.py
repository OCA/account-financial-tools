# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from freezegun import freeze_time
from odoo.tests.common import Form

from .common import TestAccountFinancialDiscountCommon


@freeze_time("2019-05-01")
class TestAccountFinancialDiscountManualPayment(
    TestAccountFinancialDiscountCommon
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client_invoice1 = cls.init_invoice(
            cls.customer,
            'out_invoice',
            payment_term=cls.payment_term,
            invoice_date='2019-05-01',
            invoice_date_due='2019-06-01',
        )
        cls.init_invoice_line(cls.client_invoice1, 1.0, 1000.0)

        cls.reconciliation_model = cls.env["account.reconcile.model"].search(
            [('rule_type', '=', 'invoice_matching')], limit=1
        )
        cls.reconciliation_model.write(
            {
                'match_partner': False,
                'strict_match_total_amount': True,
                'apply_financial_discounts': True,
                'financial_discount_tolerance': 0.05,
            }
        )
        cls.eur_bank_journal = cls.env["account.journal"].create(
            {
                "name": "Bank EUR",
                "type": "bank",
                "code": "BNK-EUR",
                "currency_id": cls.eur_currency.id,
            }
        )
        cls.reconciliation_widget = cls.env["account.reconciliation.widget"]

        cls.amount_taxed_without_discount = 1150.0
        cls.amount_taxed_discount = 23.0
        cls.amount_taxed_with_discount = 1127.0
        cls.amount_discount_tax = 3.0

        cls.amount_untaxed_without_discount = 1000.0
        cls.amount_untaxed_discount = 20.0
        cls.amount_untaxed_with_discount = 980.0

    def _create_bank_statement(self, journal=None):
        if journal is None:
            journal = self.bank_journal
        bank_statement_form = Form(self.env['account.bank.statement'])
        bank_statement_form.name = "Test Reconcile Financial Discount"
        bank_statement_form.journal_id = journal
        return bank_statement_form.save()

    def _create_bank_statement_line(self, bank_statement, label, amount):
        statement_line_form = Form(self.env['account.bank.statement.line'])
        statement_line_form.statement_id = bank_statement
        statement_line_form.name = label
        statement_line_form.amount = amount
        return statement_line_form.save()

    def test_client_invoice_with_tax_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            'out_invoice',
            payment_term=self.payment_term,
            invoice_date='2019-05-01',
            invoice_date_due='2019-06-01',
        )
        self.init_invoice_line(
            invoice, 1.0, self.amount_untaxed_without_discount
        )
        invoice.post()
        bank_statement = self._create_bank_statement()
        statement_line = self._create_bank_statement_line(
            bank_statement, invoice.name, self.amount_taxed_with_discount
        )
        rec_widget_data = self.reconciliation_widget.get_bank_statement_line_data(
            statement_line.ids
        )
        rec_widget_statement_data = rec_widget_data.get('lines')[0]
        self.assertTrue(rec_widget_statement_data.get('write_off'))
        prop = rec_widget_statement_data.get('reconciliation_proposition')[0]
        self.assertTrue(prop.get('financial_discount_available'))
        self.assertEqual(
            prop.get('amount_discount'), self.amount_taxed_discount
        )
        self.assertEqual(
            prop.get('amount_discount_tax'), self.amount_discount_tax
        )

    def test_client_invoice_without_tax_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            'out_invoice',
            payment_term=self.payment_term,
            invoice_date='2019-05-01',
            invoice_date_due='2019-06-01',
        )
        self.init_invoice_line(
            invoice, 1.0, self.amount_untaxed_without_discount, with_tax=False
        )
        invoice.post()
        bank_statement = self._create_bank_statement()
        statement_line = self._create_bank_statement_line(
            bank_statement, invoice.name, self.amount_untaxed_with_discount
        )
        rec_widget_data = self.reconciliation_widget.get_bank_statement_line_data(
            statement_line.ids
        )
        rec_widget_statement_data = rec_widget_data.get('lines')[0]
        self.assertTrue(rec_widget_statement_data.get('write_off'))
        prop = rec_widget_statement_data.get('reconciliation_proposition')[0]
        self.assertTrue(prop.get('financial_discount_available'))
        self.assertEqual(
            prop.get('amount_discount'), self.amount_untaxed_discount
        )
        self.assertEqual(prop.get('amount_discount_tax'), 0)

    def test_vendor_bill_with_tax_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            'in_invoice',
            payment_term=self.payment_term,
            invoice_date='2019-05-01',
            invoice_date_due='2019-06-01',
        )
        self.init_invoice_line(
            vendor_bill, 1.0, self.amount_untaxed_without_discount
        )
        vendor_bill.post()
        bank_statement = self._create_bank_statement()
        statement_line = self._create_bank_statement_line(
            bank_statement, vendor_bill.name, -self.amount_taxed_with_discount
        )
        rec_widget_data = self.reconciliation_widget.get_bank_statement_line_data(
            statement_line.ids
        )
        rec_widget_statement_data = rec_widget_data.get('lines')[0]
        self.assertTrue(rec_widget_statement_data.get('write_off'))
        prop = rec_widget_statement_data.get('reconciliation_proposition')[0]
        self.assertTrue(prop.get('financial_discount_available'))
        self.assertEqual(
            prop.get('amount_discount'), -self.amount_taxed_discount
        )
        self.assertEqual(
            prop.get('amount_discount_tax'), -self.amount_discount_tax
        )

    def test_vendor_bill_without_tax_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            'in_invoice',
            payment_term=self.payment_term,
            invoice_date='2019-05-01',
            invoice_date_due='2019-06-01',
        )
        self.init_invoice_line(
            vendor_bill,
            1.0,
            self.amount_untaxed_without_discount,
            with_tax=False,
        )
        vendor_bill.post()
        bank_statement = self._create_bank_statement()
        statement_line = self._create_bank_statement_line(
            bank_statement,
            vendor_bill.name,
            -self.amount_untaxed_with_discount,
        )
        rec_widget_data = self.reconciliation_widget.get_bank_statement_line_data(
            statement_line.ids
        )
        rec_widget_statement_data = rec_widget_data.get('lines')[0]
        self.assertTrue(rec_widget_statement_data.get('write_off'))
        prop = rec_widget_statement_data.get('reconciliation_proposition')[0]
        self.assertTrue(prop.get('financial_discount_available'))
        self.assertEqual(
            prop.get('amount_discount'), -self.amount_untaxed_discount
        )
        self.assertEqual(prop.get('amount_discount_tax'), 0)

    def test_client_invoice_with_tax_late_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            'out_invoice',
            payment_term=self.payment_term,
            invoice_date='2019-03-01',
            invoice_date_due='2019-04-01',
        )
        self.init_invoice_line(
            invoice, 1.0, self.amount_untaxed_without_discount
        )
        invoice.post()
        bank_statement = self._create_bank_statement()
        statement_line = self._create_bank_statement_line(
            bank_statement, invoice.name, self.amount_taxed_with_discount
        )
        rec_widget_data = self.reconciliation_widget.get_bank_statement_line_data(
            statement_line.ids
        )
        rec_widget_statement_data = rec_widget_data.get('lines')[0]
        self.assertFalse(rec_widget_statement_data.get('write_off'))
        self.assertFalse(
            rec_widget_statement_data.get('reconciliation_proposition')
        )

    def test_vendor_bill_with_tax_late_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            'in_invoice',
            payment_term=self.payment_term,
            invoice_date='2019-03-01',
            invoice_date_due='2019-04-01',
        )
        self.init_invoice_line(
            vendor_bill, 1.0, self.amount_untaxed_without_discount
        )
        vendor_bill.post()
        bank_statement = self._create_bank_statement()
        statement_line = self._create_bank_statement_line(
            bank_statement, vendor_bill.name, -self.amount_taxed_with_discount
        )
        rec_widget_data = self.reconciliation_widget.get_bank_statement_line_data(
            statement_line.ids
        )
        rec_widget_statement_data = rec_widget_data.get('lines')[0]
        self.assertFalse(rec_widget_statement_data.get('write_off'))
        self.assertFalse(
            rec_widget_statement_data.get('reconciliation_proposition')
        )

    def test_client_invoice_with_tax_late_forced_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            'out_invoice',
            payment_term=self.payment_term,
            invoice_date='2019-03-01',
            invoice_date_due='2019-04-01',
        )
        self.init_invoice_line(
            invoice, 1.0, self.amount_untaxed_without_discount
        )
        invoice.post()
        invoice.force_financial_discount = True
        bank_statement = self._create_bank_statement()
        statement_line = self._create_bank_statement_line(
            bank_statement, invoice.name, self.amount_taxed_with_discount
        )
        rec_widget_data = self.reconciliation_widget.get_bank_statement_line_data(
            statement_line.ids
        )
        rec_widget_statement_data = rec_widget_data.get('lines')[0]
        self.assertTrue(rec_widget_statement_data.get('write_off'))
        prop = rec_widget_statement_data.get('reconciliation_proposition')[0]
        self.assertTrue(prop.get('financial_discount_available'))
        self.assertEqual(
            prop.get('amount_discount'), self.amount_taxed_discount
        )
        self.assertEqual(
            prop.get('amount_discount_tax'), self.amount_discount_tax
        )

    def test_vendor_bill_with_tax_late_forced_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            'in_invoice',
            payment_term=self.payment_term,
            invoice_date='2019-03-01',
            invoice_date_due='2019-04-01',
        )
        self.init_invoice_line(
            vendor_bill, 1.0, self.amount_untaxed_without_discount
        )
        vendor_bill.force_financial_discount = True
        vendor_bill.post()
        bank_statement = self._create_bank_statement()
        statement_line = self._create_bank_statement_line(
            bank_statement, vendor_bill.name, -self.amount_taxed_with_discount
        )
        rec_widget_data = self.reconciliation_widget.get_bank_statement_line_data(
            statement_line.ids
        )
        rec_widget_statement_data = rec_widget_data.get('lines')[0]
        self.assertTrue(rec_widget_statement_data.get('write_off'))
        prop = rec_widget_statement_data.get('reconciliation_proposition')[0]
        self.assertTrue(prop.get('financial_discount_available'))
        self.assertEqual(
            prop.get('amount_discount'), -self.amount_taxed_discount
        )
        self.assertEqual(
            prop.get('amount_discount_tax'), -self.amount_discount_tax
        )

    def test_client_invoice_eur_with_tax_bank_reconciliation(self):
        invoice = self.init_invoice(
            self.customer,
            'out_invoice',
            payment_term=self.payment_term,
            invoice_date='2019-05-01',
            invoice_date_due='2019-06-01',
            currency=self.eur_currency,
        )
        self.init_invoice_line(
            invoice, 1.0, self.amount_untaxed_without_discount
        )
        invoice.post()
        bank_statement = self._create_bank_statement(
            journal=self.eur_bank_journal
        )
        statement_line = self._create_bank_statement_line(
            bank_statement, invoice.name, self.amount_taxed_with_discount
        )
        rec_widget_data = self.reconciliation_widget.get_bank_statement_line_data(
            statement_line.ids
        )
        rec_widget_statement_data = rec_widget_data.get('lines')[0]
        self.assertTrue(rec_widget_statement_data.get('write_off'))
        prop = rec_widget_statement_data.get('reconciliation_proposition')[0]
        self.assertTrue(prop.get('financial_discount_available'))
        self.assertEqual(
            prop.get('amount_discount'),
            self.eur_currency._convert(
                self.amount_taxed_discount,
                self.usd_currency,
                invoice.company_id,
                invoice.invoice_date,
            ),
        )
        self.assertEqual(
            prop.get('amount_discount_currency'), self.amount_taxed_discount
        )
        self.assertEqual(
            prop.get('amount_discount_tax'),
            self.eur_currency._convert(
                self.amount_discount_tax,
                self.usd_currency,
                invoice.company_id,
                invoice.invoice_date,
            ),
        )

    def test_vendor_bill_eur_with_tax_bank_reconciliation(self):
        vendor_bill = self.init_invoice(
            self.partner,
            'in_invoice',
            payment_term=self.payment_term,
            invoice_date='2019-05-01',
            invoice_date_due='2019-06-01',
            currency=self.eur_currency,
        )
        self.init_invoice_line(
            vendor_bill, 1.0, self.amount_untaxed_without_discount
        )
        vendor_bill.post()
        bank_statement = self._create_bank_statement(
            journal=self.eur_bank_journal
        )
        statement_line = self._create_bank_statement_line(
            bank_statement, vendor_bill.name, -self.amount_taxed_with_discount
        )
        rec_widget_data = self.reconciliation_widget.get_bank_statement_line_data(
            statement_line.ids
        )
        rec_widget_statement_data = rec_widget_data.get('lines')[0]
        self.assertTrue(rec_widget_statement_data.get('write_off'))
        prop = rec_widget_statement_data.get('reconciliation_proposition')[0]
        self.assertTrue(prop.get('financial_discount_available'))
        self.assertEqual(
            prop.get('amount_discount'),
            self.eur_currency._convert(
                -self.amount_taxed_discount,
                self.usd_currency,
                vendor_bill.company_id,
                vendor_bill.invoice_date,
            ),
        )
        self.assertEqual(
            prop.get('amount_discount_currency'), -self.amount_taxed_discount
        )
        self.assertEqual(
            prop.get('amount_discount_tax'),
            self.eur_currency._convert(
                -self.amount_discount_tax,
                self.usd_currency,
                vendor_bill.company_id,
                vendor_bill.invoice_date,
            ),
        )

    # TODO add more tests with banking reconciliation:
    #  - Auto-reconcile on the model
    #  - Test JS?
