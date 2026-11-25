# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields
from odoo.tests import tagged

from .common import TestAccountMoveFromEPDCommon


@tagged("post_install", "-at_install")
class TestAccountMoveFromEPD(TestAccountMoveFromEPDCommon):
    """Test suite for account_move_from_epd.

    Scenario:
    - Customer invoice with 2 lines totalling 1000.0 (taxes excluded)
    - Payment term: 5% EPD if paid within 10 days, net 30
    - A partial credit note of 200.0 is posted and reconciled against the invoice
    - The wizard should generate a journal entry that materialises the EPD
      (50.0) as if the customer had paid in full within the discount window,
      without the refund having been issued.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Customer invoice: 2 lines, taxes cleared for predictable totals.
        # Line 1: qty 2 × 300 = 600
        # Line 2: qty 1 × 400 = 400
        # Total  : 1 000.0   EPD (5%) : 50.0
        cls.invoice = cls._create_invoice(
            "out_invoice",
            [(cls.product_a, 2, 300, []), (cls.product_b, 1, 400, [])],
            extra_values={"invoice_payment_term_id": cls.payment_term_epd.id},
        )
        # Partial credit note: 200.0
        cls.refund = cls._create_invoice("out_refund", [(cls.product_b, 1, 200, [])])
        # Reconcile the credit note against the invoice's receivable lines.
        cls._reconcile([cls.invoice, cls.refund])

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_wizard_generates_epd_move(self):
        """Executing the wizard must create a posted journal entry that
        materialises the 5% early payment discount (50.0) on the invoice.

        The generated move should:
        - be posted in the requested journal on the requested date
        - contain a receivable line that credits 50.0 (reducing what the
          customer owes, equivalent to granting the discount)
        - contain a counter-line on the EPD write-off account for 50.0
        - leave the invoice residual at 750.0 (800 − 50)
        """
        self.assertEqual(self.invoice.state, "posted")
        self.assertAlmostEqual(self.invoice.amount_total, 1000.0)
        self.assertAlmostEqual(self.invoice.amount_residual, 800.0)

        wizard = self._create_wizard(self.invoice)
        result = wizard.action_generate()

        # The wizard is expected to return an ir.actions.act_window dict
        # pointing to the newly created account.move.
        self.assertIsNotNone(result, "action_generate() must return a result")
        epd_move = self.env["account.move"].browse(result["res_id"])
        self.assertTrue(epd_move.exists(), "EPD move should exist")

        # State and meta-data
        self.assertEqual(epd_move.state, "posted")
        self.assertEqual(epd_move.journal_id, self.journal_misc)
        self.assertEqual(epd_move.date, fields.Date.today())
        self.assertEqual(epd_move.partner_id, self.partner_a)

        # Amounts: EPD = 5% of invoice total = 1 000 × 5% = 50.0
        expected_epd_amount = self.invoice.amount_total * 0.05
        receivable_lines = epd_move.line_ids.filtered(
            lambda li: li.account_id.account_type == "asset_receivable"
        )
        self.assertAlmostEqual(
            sum(receivable_lines.mapped("credit")),
            expected_epd_amount,
            msg="Receivable credit on EPD move should equal the discount amount",
        )

        epd_account_lines = epd_move.line_ids.filtered(
            lambda li: li.account_id == self.epd_loss_account
        )
        self.assertAlmostEqual(
            sum(epd_account_lines.mapped("debit")),
            expected_epd_amount,
            msg="Write-off debit on EPD move should equal the discount amount",
        )

        # After EPD materialisation the invoice residual should drop to 750.0
        self.assertAlmostEqual(
            self.invoice.amount_residual,
            800.0 - expected_epd_amount,
            msg="Invoice residual should be reduced by the EPD amount",
        )


@tagged("post_install", "-at_install")
class TestAccountMoveFromEPDMulticurrency(TestAccountMoveFromEPDCommon):
    """Multi-currency variant: invoice denominated in a foreign currency.

    Scenario:
    - Company currency : USD (default for AccountTestInvoicingCommon)
    - Invoice currency : EUR at rate 2.0  (1 EUR = 2 company-currency units)
    - Invoice total    : 1 000 EUR = 2 000 USD
    - EPD              : 5 % → 50 EUR = 100 USD
    - Partial refund   : 200 EUR = 400 USD
    - Residual after refund : 800 EUR / 1 600 USD
    - After wizard     : 750 EUR / 1 500 USD

    The test derives expected amounts from the stored payment-term line so it
    stays correct regardless of rounding or rate conventions.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # EUR at a fixed rate of 2.0 relative to the company currency so that
        # assertions are easy to reason about.
        cls.eur = cls.setup_other_currency(
            "EUR",
            rates=[(str(fields.Date.today()), 2.0)],
        )
        # Invoice in EUR: 2 lines, no taxes, total = 1 000 EUR
        cls.invoice = cls._create_invoice(
            "out_invoice",
            [(cls.product_a, 2, 300, []), (cls.product_b, 1, 400, [])],
            extra_values={
                "invoice_payment_term_id": cls.payment_term_epd.id,
                "currency_id": cls.eur.id,
            },
        )

        # Capture EPD amounts from the stored payment-term line so assertions
        # are independent of rate-rounding implementation details.
        ptl = cls.invoice.line_ids.filtered(
            lambda li: li.display_type == "payment_term"
        )
        cls.expected_epd_amount_currency = abs(
            ptl.amount_currency - ptl.discount_amount_currency
        )
        cls.expected_epd_balance = abs(ptl.balance - ptl.discount_balance)

        # Partial credit note: 200 EUR
        cls.refund = cls._create_invoice(
            "out_refund",
            [(cls.product_b, 1, 200, [])],
            extra_values={"currency_id": cls.eur.id},
        )
        # Reconcile the credit note against the invoice's receivable lines.
        cls._reconcile([cls.invoice, cls.refund])

    def test_multicurrency_wizard_generates_epd_move(self):
        """EPD move amounts must be correct in both invoice currency and company
        currency (balance).

        The wizard uses the payment-term line's stored ``balance`` /
        ``amount_currency`` delta so the company-currency conversion is always
        consistent with the invoice's own exchange rate, avoiding any
        discrepancy caused by the EPD entry being posted on a different date.
        """
        self.assertEqual(self.invoice.state, "posted")
        self.assertAlmostEqual(self.invoice.amount_total, 1000.0)
        self.assertAlmostEqual(self.invoice.amount_residual, 800.0)

        wizard = self._create_wizard(self.invoice)
        result = wizard.action_generate()

        epd_move = self.env["account.move"].browse(result["res_id"])
        self.assertTrue(epd_move.exists())
        self.assertEqual(epd_move.state, "posted")
        self.assertEqual(epd_move.journal_id, self.journal_misc)
        self.assertEqual(epd_move.partner_id, self.partner_a)

        receivable_lines = epd_move.line_ids.filtered(
            lambda li: li.account_id.account_type == "asset_receivable"
        )

        # Invoice-currency amount (amount_currency) — should match the 5% EPD
        self.assertAlmostEqual(
            abs(sum(receivable_lines.mapped("amount_currency"))),
            self.expected_epd_amount_currency,
            msg="EPD receivable line amount_currency should match the discount "
            "in invoice currency",
        )

        # Company-currency amount (balance) — derived from the invoice rate
        self.assertAlmostEqual(
            abs(sum(receivable_lines.mapped("balance"))),
            self.expected_epd_balance,
            msg="EPD receivable line balance should match the discount in "
            "company currency at the invoice's exchange rate",
        )

        # Invoice residual (in invoice currency) drops by the EPD amount
        self.assertAlmostEqual(
            self.invoice.amount_residual,
            800.0 - self.expected_epd_amount_currency,
            msg="Invoice residual should be reduced by the EPD amount in "
            "invoice currency",
        )


@tagged("post_install", "-at_install")
class TestAccountMoveFromEPDWithTax(TestAccountMoveFromEPDCommon):
    """EPD move generation when the invoice carries taxes (single currency).

    With ``early_pay_discount_computation = 'included'`` the wizard must emit
    separate base-amount and tax write-off lines so that the tax report is
    updated correctly.

    Scenario:
    - Customer invoice: product_a (carries tax_sale_a by default), qty 2 × 1000
    - Payment term   : 5% EPD within 10 days
    - No partial refund → percentage_paid = 1.0, guaranteeing exact tax split
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # product_a carries tax_sale_a by default — no need to set tax_ids.
        cls.invoice = cls._create_invoice(
            "out_invoice",
            [(cls.product_a, 2, 1000, [(6, 0, cls.tax_sale_a.ids)])],
            extra_values={"invoice_payment_term_id": cls.payment_term_epd.id},
        )
        # Capture EPD amounts from the stored payment-term line.
        ptl = cls.invoice.line_ids.filtered(
            lambda li: li.display_type == "payment_term"
        )
        cls.ptl = ptl
        cls.expected_epd_balance = ptl.balance - ptl.discount_balance
        cls.expected_epd_amount_currency = (
            ptl.amount_currency - ptl.discount_amount_currency
        )

    def test_epd_move_with_tax_has_tax_lines(self):
        """Generated EPD move must contain separate base and tax write-off lines."""
        initial_residual = self.invoice.amount_residual

        wizard = self._create_wizard(self.invoice)
        result = wizard.action_generate()

        self.assertIsNotNone(result)
        epd_move = self.env["account.move"].browse(result["res_id"])
        self.assertTrue(epd_move.exists())
        self.assertEqual(epd_move.state, "posted")
        self.assertEqual(epd_move.partner_id, self.partner_a)

        receivable_account = self.ptl.account_id
        ar_lines = epd_move.line_ids.filtered(
            lambda li: li.account_id == receivable_account
        )
        non_ar_lines = epd_move.line_ids - ar_lines

        # With 'included' + taxes there must be at least a base and a tax line.
        self.assertGreaterEqual(
            len(non_ar_lines),
            2,
            "EPD move should have at least 2 non-AR lines (base + tax)",
        )

        # At least one EPD line must carry a tax_repartition_line_id.
        tax_lines = non_ar_lines.filtered(lambda li: li.tax_repartition_line_id)
        self.assertTrue(
            tax_lines,
            "At least one EPD line must have tax_repartition_line_id set",
        )

        # Helper rounding fix guarantees sum(base+tax lines) == term_balance.
        self.assertAlmostEqual(
            sum(non_ar_lines.mapped("balance")),
            self.expected_epd_balance,
            places=2,
            msg="Sum of non-AR EPD line balances must equal the full EPD balance",
        )

        # Invoice residual drops by the full EPD amount.
        self.assertAlmostEqual(
            self.invoice.amount_residual,
            initial_residual - self.expected_epd_amount_currency,
            places=2,
            msg="Invoice residual should drop by the EPD amount",
        )


@tagged("post_install", "-at_install")
class TestAccountMoveFromEPDMulticurrencyWithTax(TestAccountMoveFromEPDCommon):
    """Multi-currency EPD move generation with taxes.

    Same scenario as TestAccountMoveFromEPDWithTax but the invoice is
    denominated in EUR (rate 2.0), verifying that both ``amount_currency``
    and ``balance`` are correct across all write-off lines.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.eur = cls.setup_other_currency(
            "EUR",
            rates=[(str(fields.Date.today()), 2.0)],
        )

        # Invoice in EUR with product_a (tax_sale_a by default).
        cls.invoice = cls._create_invoice(
            "out_invoice",
            [(cls.product_a, 2, 1000, [(6, 0, cls.tax_sale_a.ids)])],
            extra_values={
                "invoice_payment_term_id": cls.payment_term_epd.id,
                "currency_id": cls.eur.id,
            },
        )

        ptl = cls.invoice.line_ids.filtered(
            lambda li: li.display_type == "payment_term"
        )
        cls.ptl_mc = ptl
        cls.expected_epd_balance = ptl.balance - ptl.discount_balance
        cls.expected_epd_amount_currency = (
            ptl.amount_currency - ptl.discount_amount_currency
        )

    def test_mc_epd_move_with_tax_has_tax_lines(self):
        """Generated EPD move must have tax lines and correct amounts in both
        EUR and company currency."""
        initial_residual = self.invoice.amount_residual

        wizard = self._create_wizard(self.invoice)
        result = wizard.action_generate()

        self.assertIsNotNone(result)
        epd_move = self.env["account.move"].browse(result["res_id"])
        self.assertTrue(epd_move.exists())
        self.assertEqual(epd_move.state, "posted")
        self.assertEqual(epd_move.partner_id, self.partner_a)

        receivable_account = self.ptl_mc.account_id
        ar_lines = epd_move.line_ids.filtered(
            lambda li: li.account_id == receivable_account
        )
        non_ar_lines = epd_move.line_ids - ar_lines

        self.assertGreaterEqual(
            len(non_ar_lines),
            2,
            "EPD move should have at least 2 non-AR lines (base + tax)",
        )

        tax_lines = non_ar_lines.filtered(lambda li: li.tax_repartition_line_id)
        self.assertTrue(
            tax_lines,
            "At least one EPD line must have tax_repartition_line_id set",
        )

        # Sum of non-AR balances (company currency) == stored EPD balance.
        self.assertAlmostEqual(
            sum(non_ar_lines.mapped("balance")),
            self.expected_epd_balance,
            places=2,
            msg="Sum of non-AR EPD line balances must equal the full EPD balance "
            "in company currency",
        )

        # Sum of non-AR amount_currency (EUR) == stored EPD amount_currency.
        self.assertAlmostEqual(
            sum(non_ar_lines.mapped("amount_currency")),
            self.expected_epd_amount_currency,
            places=2,
            msg="Sum of non-AR EPD line amount_currency must equal the full EPD "
            "amount in invoice currency",
        )

        # Invoice residual (in EUR) drops by the full EPD amount.
        self.assertAlmostEqual(
            self.invoice.amount_residual,
            initial_residual - self.expected_epd_amount_currency,
            places=2,
            msg="Invoice residual should drop by the EPD amount in invoice currency",
        )
