# Copyright 2024 Som IT Cooperatiu SCCL - Nicolás Ramos <nicolas.ramos@somit.coop>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestLoanPermanent(TransactionCase):
    def setUp(self):
        super(TestLoanPermanent, self).setUp()
        self.loan_model = self.env["account.loan"]
        self.loan_line_model = self.env["account.loan.line"]
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})

        # Buscar cuentas apropiadas
        self.short_term_account = self.env["account.account"].search(
            [("account_type", "=", "liability_payable")], limit=1
        )
        self.interest_account = self.env["account.account"].search(
            [("account_type", "=", "expense")], limit=1
        )

        # Create a test loan
        self.test_loan = self.loan_model.create(
            {
                "name": "Test Permanent Loan",
                "loan_type": "interest",
                "is_permanent": True,
                "company_id": self.env.company.id,
                "partner_id": self.partner.id,
                "journal_id": self.env["account.journal"]
                .search([("type", "=", "general")], limit=1)
                .id,
                "loan_amount": 10000,
                "rate": 5,
                "start_date": fields.Date.today(),
                "periods": 12,
                "min_periods": 60,
                "short_term_loan_account_id": self.short_term_account.id,
                "interest_expenses_account_id": self.interest_account.id,
            }
        )

    def test_onchange_is_permanent(self):
        """Test the onchange behavior of is_permanent field"""
        self.test_loan.loan_type = "fixed-annuity"
        self.test_loan._onchange_is_permanent()
        self.assertFalse(self.test_loan.is_permanent)

        self.test_loan.loan_type = "interest"
        self.test_loan.is_permanent = True
        self.test_loan._onchange_is_permanent()
        self.assertEqual(self.test_loan.residual_amount, 0)
        self.assertEqual(self.test_loan.periods, 60)  # max(12, 60)

        # Test when periods is greater than min_periods
        self.test_loan.periods = 80
        self.test_loan._onchange_is_permanent()
        self.assertEqual(self.test_loan.periods, 80)  # max(80, 60)

    def test_onchange_is_permanent_warning(self):
        """Test warning when setting is_permanent with invalid loan_type."""
        self.test_loan.loan_type = "fixed-annuity"
        warning = self.test_loan._onchange_is_permanent()
        self.assertFalse(self.test_loan.is_permanent)
        self.assertIn("Invalid Loan Type", warning["warning"]["title"])

    def test_create_permanent_loan(self):
        """Test the creation of a permanent loan"""
        loan = self.loan_model.create(
            {
                "name": "New Permanent Loan",
                "loan_type": "interest",
                "is_permanent": True,
                "company_id": self.env.company.id,
                "partner_id": self.partner.id,
                "journal_id": self.env["account.journal"]
                .search([("type", "=", "general")], limit=1)
                .id,
                "loan_amount": 20000,
                "rate": 4,
                "start_date": fields.Date.today(),
                "periods": 24,
                "min_periods": 60,
                "short_term_loan_account_id": self.short_term_account.id,
                "interest_expenses_account_id": self.interest_account.id,
            }
        )
        self.assertEqual(loan.periods, 60)

    def test_create_permanent_loan_min_periods(self):
        """Test that a permanent loan respects min_periods on creation."""
        loan = self.loan_model.create(
            {
                "name": "New Permanent Loan",
                "loan_type": "interest",
                "is_permanent": True,
                "company_id": self.env.company.id,
                "partner_id": self.partner.id,
                "journal_id": self.env["account.journal"]
                .search([("type", "=", "general")], limit=1)
                .id,
                "loan_amount": 20000,
                "rate": 4,
                "start_date": fields.Date.today(),
                "periods": 24,
                "min_periods": 60,
                "short_term_loan_account_id": self.short_term_account.id,
                "interest_expenses_account_id": self.interest_account.id,
            }
        )
        self.assertEqual(loan.periods, 60)

    def test_generate_loan_entries(self):
        """Test the generation of loan entries for permanent loans"""
        self.test_loan.start_date = fields.Date.today() - relativedelta(months=3)
        self.test_loan.post()

        future_date = fields.Date.today() + relativedelta(months=6)
        self.loan_model._generate_loan_entries(future_date)

        self.assertEqual(len(self.test_loan.line_ids), 69)  # 3 past + 6 future + 60 min
        self.assertEqual(self.test_loan.periods, 69)

    def test_ensure_min_periods(self):
        """Test ensuring minimum periods for permanent loans"""
        self.test_loan.start_date = fields.Date.today() - relativedelta(months=1)
        self.test_loan.post()

        last_line = self.test_loan.line_ids.sorted(key=lambda r: r.sequence)[-1]
        last_line._ensure_min_periods()

        self.assertEqual(len(self.test_loan.line_ids), 61)  # 1 past + 60 min
        self.assertEqual(self.test_loan.periods, 61)

    def test_create_next_line(self):
        """Test creating the next line for a permanent loan"""
        self.test_loan.post()
        last_line = self.test_loan.line_ids.sorted(key=lambda r: r.sequence)[-1]

        new_line = self.loan_line_model._create_next_line(last_line)

        self.assertEqual(new_line.sequence, last_line.sequence + 1)
        self.assertEqual(new_line.date, last_line.date + relativedelta(months=1))
        self.assertEqual(new_line.rate, last_line.rate)
        self.assertEqual(
            new_line.pending_principal_amount, last_line.final_pending_principal_amount
        )

    def test_onchange_is_permanent_with_interest_type(self):
        """Test onchange behavior when loan type is 'interest'."""
        self.test_loan.loan_type = "interest"
        self.test_loan.is_permanent = True
        self.test_loan._onchange_is_permanent()
        self.assertTrue(self.test_loan.is_permanent)
        self.assertEqual(self.test_loan.residual_amount, 0)
        self.assertGreaterEqual(self.test_loan.periods, self.test_loan.min_periods)

    def test_generate_loan_entries_for_permanent_loan(self):
        """Test generation of loan entries for permanent loans."""
        self.test_loan.start_date = fields.Date.today() - relativedelta(months=2)
        self.test_loan.post()
        future_date = fields.Date.today() + relativedelta(months=3)
        self.loan_model._generate_loan_entries(future_date)
        self.assertGreater(len(self.test_loan.line_ids), self.test_loan.min_periods)
        last_line = self.test_loan.line_ids.sorted(key=lambda r: r.sequence)[-1]
        self.assertGreater(last_line.date, future_date)

    def test_create_next_line_for_permanent_loan(self):
        """Test creation of next line for permanent loans."""
        self.test_loan.post()
        last_line = self.test_loan.line_ids.sorted(key=lambda r: r.sequence)[-1]
        new_line = self.env["account.loan.line"]._create_next_line(last_line)
        self.assertEqual(new_line.sequence, last_line.sequence + 1)
        self.assertEqual(new_line.date, last_line.date + relativedelta(months=1))
        self.assertEqual(new_line.pending_principal_amount, self.test_loan.loan_amount)
        self.assertEqual(
            new_line.long_term_pending_principal_amount, self.test_loan.loan_amount
        )

    def test_compute_interests_for_permanent_loan(self):
        """Test interest computation for permanent loans."""
        self.test_loan.post()
        line = self.test_loan.line_ids[0]
        line._compute_interests()
        expected_interest = (
            self.test_loan.loan_amount * self.test_loan.rate_period / 100
        )
        self.assertAlmostEqual(line.interests_amount, expected_interest, places=2)

    def test_compute_amount_for_permanent_loan(self):
        """Test amount computation for permanent loans."""
        self.test_loan.post()
        line = self.test_loan.line_ids[0]
        line._compute_amount()
        self.assertEqual(line.payment_amount, line.interests_amount)
        self.assertEqual(line.principal_amount, 0)
        self.assertEqual(line.pending_principal_amount, self.test_loan.loan_amount)
        self.assertEqual(
            line.final_pending_principal_amount, self.test_loan.loan_amount
        )
