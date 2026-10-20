# Copyright 2026 INVITU
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account_loan.tests.test_loan import TestLoan


@tagged("post_install", "-at_install")
class TestLoanExtraCost(TestLoan):
    """Tests for the Extra Costs feature added on top of account.loan."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.insurance_account = cls.create_account(
            "INS", "Insurance expenses", "expense"
        )
        cls.upfront_fee_account = cls.create_account("UFEE", "Upfront fees", "expense")

    def _add_extra_cost(self, loan, **vals):
        defaults = {
            "loan_id": loan.id,
            "name": "Insurance",
            "payment_type": "periodic",
            "calculation_method": "fixed",
            "amount": 0.0,
            "rate": 0.0,
            "account_id": self.insurance_account.id,
        }
        defaults.update(vals)
        return self.env["account.loan.extra.cost"].create(defaults)

    # ------------------------------------------------------------------
    # Calculation methods
    # ------------------------------------------------------------------

    def test_extra_cost_fixed_amount(self):
        loan = self.create_loan("fixed-principal", 15000000, 6, 60)
        self._add_extra_cost(loan, amount=100.0)
        loan.compute_lines()
        for line in loan.line_ids:
            self.assertEqual(line.extra_cost_amount, 100.0)

    def test_extra_cost_rate_initial_capital(self):
        loan = self.create_loan("fixed-principal", 15000000, 6, 60)
        self._add_extra_cost(loan, calculation_method="rate_initial_capital", rate=0.36)
        loan.compute_lines()
        expected = 15000000 * 0.36 / 100 / 12
        for line in loan.line_ids:
            self.assertEqual(line.extra_cost_amount, expected)

    def test_extra_cost_rate_remaining_per_period(self):
        loan = self.create_loan("fixed-principal", 15000000, 6, 60)
        self._add_extra_cost(
            loan,
            calculation_method="rate_remaining_per_period",
            rate=0.36,
        )
        loan.compute_lines()
        for line in loan.line_ids:
            expected = round(line.pending_principal_amount * 0.36 / 100 / 12, 2)
            self.assertEqual(line.extra_cost_amount, expected)

    def test_extra_cost_rate_remaining_annual(self):
        loan = self.create_loan("fixed-principal", 15000000, 6, 60)
        self._add_extra_cost(
            loan, calculation_method="rate_remaining_annual", rate=0.36
        )
        loan.compute_lines()
        line1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        # Within year 1, all 12 lines share the same extra cost amount
        for seq in range(1, 13):
            line = loan.line_ids.filtered(lambda r, seq=seq: r.sequence == seq)
            self.assertEqual(line.extra_cost_amount, line1.extra_cost_amount)
        # Within year 2, all 12 lines share another (smaller) amount
        line13 = loan.line_ids.filtered(lambda r: r.sequence == 13)
        for seq in range(13, 25):
            line = loan.line_ids.filtered(lambda r, seq=seq: r.sequence == seq)
            self.assertEqual(line.extra_cost_amount, line13.extra_cost_amount)
        self.assertLess(line13.extra_cost_amount, line1.extra_cost_amount)

    # ------------------------------------------------------------------
    # payment_amount aggregation
    # ------------------------------------------------------------------

    def test_payment_amount_includes_extra_cost(self):
        loan = self.create_loan("fixed-principal", 15000000, 6, 60)
        self._add_extra_cost(loan, amount=100.0)
        loan.compute_lines()
        for line in loan.line_ids:
            self.assertEqual(
                line.payment_amount,
                line.principal_amount + line.interests_amount + line.extra_cost_amount,
            )

    # ------------------------------------------------------------------
    # Journal entry generation
    # ------------------------------------------------------------------

    def test_periodic_extra_cost_in_move(self):
        loan = self.create_loan("fixed-principal", 15000000, 6, 60)
        self._add_extra_cost(loan, amount=100.0)
        loan.compute_lines()
        self.partner.property_account_payable_id = self.payable_account
        self.post(loan)
        line1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line1._generate_move()
        move = line1.move_ids
        insurance_lines = move.line_ids.filtered(
            lambda r: r.account_id == self.insurance_account
        )
        self.assertEqual(len(insurance_lines), 1)
        self.assertEqual(insurance_lines.debit, 100.0)

    def test_upfront_extra_cost_in_post(self):
        loan = self.create_loan("fixed-principal", 15000000, 6, 60)
        self._add_extra_cost(
            loan,
            name="Application fee",
            payment_type="upfront",
            amount=5000.0,
            account_id=self.upfront_fee_account.id,
        )
        loan.compute_lines()
        self.partner.property_account_payable_id = self.payable_account
        self.post(loan)
        move = loan.move_ids
        fee_line = move.line_ids.filtered(
            lambda r: r.account_id == self.upfront_fee_account
        )
        self.assertEqual(fee_line.debit, 5000.0)
        # Same upfront amount is credited back on the opening account
        opening_lines = move.line_ids.filtered(
            lambda r: r.account_id == self.partner.property_account_receivable_id
        )
        self.assertEqual(sum(opening_lines.mapped("credit")), 5000.0)

    # ------------------------------------------------------------------
    # Wizards skip extra costs
    # ------------------------------------------------------------------

    def test_pay_amount_line_skips_extra_cost(self):
        loan = self.create_loan("fixed-principal", 15000000, 6, 60)
        self._add_extra_cost(loan, amount=100.0)
        loan.compute_lines()
        self.partner.property_account_payable_id = self.payable_account
        self.post(loan)
        line1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line1._generate_move()
        line2 = loan.line_ids.filtered(lambda r: r.sequence == 2)
        self.env["account.loan.pay.amount"].create(
            {
                "loan_id": loan.id,
                "amount": 1000.0,
                "date": line2.date,
                "fees": 0.0,
            }
        ).run()
        manual_line = loan.line_ids.filtered("is_manual_payment")
        self.assertTrue(manual_line)
        self.assertEqual(manual_line.extra_cost_amount, 0.0)

    # ------------------------------------------------------------------
    # Leasing scenario
    # ------------------------------------------------------------------

    def test_periodic_extra_cost_in_invoice(self):
        """Each periodic extra cost generates its own line in the invoice."""
        loan = self.create_loan("fixed-principal", 24000, 1, 24)
        loan.is_leasing = True
        loan.post_invoice = False
        loan.rate_type = "real"
        self._add_extra_cost(loan, amount=50.0)
        loan.compute_lines()
        self.partner.property_account_payable_id = self.payable_account
        self.post(loan)
        self.env["account.loan.generate.wizard"].create(
            {
                "date": fields.date.today() + relativedelta(days=1),
                "loan_type": "leasing",
            }
        ).run()
        line1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line1.has_invoices)
        invoice = line1.move_ids.filtered(lambda m: m.is_invoice())
        self.assertEqual(len(invoice), 1)
        # The invoice has one dedicated line on the insurance account
        insurance_lines = invoice.invoice_line_ids.filtered(
            lambda r: r.account_id == self.insurance_account
        )
        self.assertEqual(len(insurance_lines), 1)
        self.assertEqual(insurance_lines.price_unit, 50.0)
