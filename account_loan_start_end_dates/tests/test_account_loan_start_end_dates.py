# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from dateutil.relativedelta import relativedelta

from odoo.tests import tagged

from odoo.addons.account_loan.tests.common import LoanCommon


@tagged("post_install", "-at_install")
class TestAccountLoanStartEndDates(LoanCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_sequence_starts_one(self):
        amount = 10000
        periods = 24
        loan = self.create_loan(
            loan_method="fixed-annuity",
            amount=amount,
            rate=1,
            periods=periods,
            loan_type="loan",
        )
        self.assertTrue(loan.line_ids)
        self.post(loan)
        line = loan.line_ids[0]
        line.view_process_values()
        moves = line.move_ids
        move_lines = moves.mapped("line_ids")
        interests_line = move_lines.filtered(
            lambda ml: ml.account_id.id == loan.interest_expenses_account_id.id
        )
        start_date = loan.start_date
        end_date = line.date
        self.assertEqual(interests_line.start_date, start_date)
        self.assertEqual(interests_line.end_date, end_date)

    def test_sequence_starts_greater_than_one(self):
        amount = 10000
        periods = 24
        loan = self.create_loan(
            loan_method="fixed-annuity",
            amount=amount,
            rate=1,
            periods=periods,
            loan_type="loan",
        )
        self.assertTrue(loan.line_ids)
        self.post(loan)
        lines = loan.line_ids
        loan.line_ids = lines[2:]

        line = loan.line_ids[0]
        line.view_process_values()
        moves = line.move_ids
        move_lines = moves.mapped("line_ids")
        interests_line = move_lines.filtered(
            lambda ml: ml.account_id.id == loan.interest_expenses_account_id.id
        )

        start_date = line.date - relativedelta(months=1) + relativedelta(days=1)
        end_date = line.date

        self.assertEqual(interests_line.start_date, start_date)
        self.assertEqual(interests_line.end_date, end_date)

    def test_sequence_starts_greater_than_one_multiple_method_period(self):
        amount = 10000
        periods = 24
        method_period = 3
        loan = self.create_loan(
            loan_method="fixed-annuity",
            amount=amount,
            rate=1,
            periods=periods,
            loan_type="loan",
        )
        loan.method_period = method_period
        self.assertTrue(loan.line_ids)
        self.post(loan)
        lines = loan.line_ids
        loan.line_ids = lines[2:]

        line = loan.line_ids[0]
        line.view_process_values()
        moves = line.move_ids
        move_lines = moves.mapped("line_ids")
        interests_line = move_lines.filtered(
            lambda ml: ml.account_id.id == loan.interest_expenses_account_id.id
        )

        start_date = (
            line.date - relativedelta(months=method_period) + relativedelta(days=1)
        )
        end_date = line.date

        self.assertEqual(interests_line.start_date, start_date)
        self.assertEqual(interests_line.end_date, end_date)

    def test_not_first_line(self):
        amount = 10000
        periods = 24
        loan = self.create_loan(
            loan_method="fixed-annuity",
            amount=amount,
            rate=1,
            periods=periods,
            loan_type="loan",
        )
        self.assertTrue(loan.line_ids)
        self.post(loan)
        # We need to compute moves in the order of lines to prevent error
        previous_line = loan.line_ids[0]
        previous_line.view_process_values()
        # Compute the line we want:
        line = loan.line_ids[1]
        line.view_process_values()
        moves = line.move_ids
        move_lines = moves.mapped("line_ids")
        interests_line = move_lines.filtered(
            lambda ml: ml.account_id.id == loan.interest_expenses_account_id.id
        )

        previous_line = loan.line_ids[0]
        start_date = previous_line.date + relativedelta(days=1)
        end_date = line.date

        self.assertEqual(interests_line.start_date, start_date)
        self.assertEqual(interests_line.end_date, end_date)

    def test_advance_payment(self):
        amount = 10000
        periods = 24
        method_period = 2
        loan = self.create_loan(
            loan_method="fixed-annuity",
            amount=amount,
            rate=1,
            periods=periods,
            loan_type="loan",
        )
        loan.write({"advance_payment": True, "method_period": method_period})
        self.assertTrue(loan.line_ids)
        self.post(loan)
        for line in loan.line_ids:
            line.view_process_values()
        line = loan.line_ids[0]
        moves = line.move_ids
        move_lines = moves.mapped("line_ids")
        interests_line = move_lines.filtered(
            lambda ml: ml.account_id.id == loan.interest_expenses_account_id.id
        )
        start_date = line.date
        end_date = (
            line.date + relativedelta(months=method_period) - relativedelta(days=1)
        )

        self.assertEqual(interests_line.start_date, start_date)
        self.assertEqual(interests_line.end_date, end_date)

        last_line = loan.line_ids[-1]
        moves = last_line.move_ids
        move_lines = moves.mapped("line_ids")
        interests_line = move_lines.filtered(
            lambda ml: ml.account_id.id == loan.interest_expenses_account_id.id
        )
        self.assertFalse(interests_line.start_date)
        self.assertFalse(interests_line.end_date)
