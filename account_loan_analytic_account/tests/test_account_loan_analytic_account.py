# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.account_loan.tests.common import LoanCommon


class TestAccountLoanAnalyticAccount(LoanCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids += cls.env.ref("analytic.group_analytic_accounting")

        cls.default_plan = cls.env["account.analytic.plan"].create({"name": "Default"})
        cls.analytic_account_a = cls.env["account.analytic.account"].create(
            {
                "name": "analytic_account_a",
                "plan_id": cls.default_plan.id,
            }
        )
        cls.analytic_account_b = cls.env["account.analytic.account"].create(
            {
                "name": "analytic_account_b",
                "plan_id": cls.default_plan.id,
            }
        )
        cls.analytic_account_c = cls.env["account.analytic.account"].create(
            {
                "name": "analytic_account_c",
                "plan_id": cls.default_plan.id,
            }
        )

    def setUp(self):
        super().setUp()
        self.loan = self.create_loan(
            "fixed-annuity", 500000, 1, 60, compute_lines=False
        )
        self.loan.write(
            {
                "analytic_distribution": {
                    self.analytic_account_a.id: 50,
                    self.analytic_account_b.id: 50,
                }
            }
        )
        self.loan.compute_lines()

    def test_analytic_account_propagates_to_moves(self):
        post = (
            self.env["account.loan.post"]
            .with_context(default_loan_id=self.loan.id)
            .create({})
        )
        post.run()

        self.assertTrue(self.loan.move_ids)

        loan_line = self.loan.line_ids.filtered(lambda r: r.sequence == 1)
        loan_line.view_process_values()
        move_lines = loan_line.move_ids.mapped("line_ids")
        self.assertTrue(loan_line.move_ids)
        for line in move_lines:
            if line.account_id == self.loan.interest_expenses_account_id:
                self.assertEqual(
                    line.analytic_distribution, self.loan.analytic_distribution
                )

    def test_analytic_account_propagates_to_moves_after_validation(self):
        post = (
            self.env["account.loan.post"]
            .with_context(default_loan_id=self.loan.id)
            .create({})
        )
        post.run()

        self.assertTrue(self.loan.move_ids)

        loan_line = self.loan.line_ids.filtered(lambda r: r.sequence == 1)
        loan_line.view_process_values()
        move_lines = loan_line.move_ids.mapped("line_ids")
        self.assertTrue(loan_line.move_ids)
        self.loan.write(
            {
                "analytic_distribution": {
                    self.analytic_account_a.id: 50,
                    self.analytic_account_c.id: 50,
                },
            }
        )
        for line in move_lines:
            if line.account_id == self.loan.interest_expenses_account_id:
                self.assertEqual(
                    line.analytic_distribution, self.loan.analytic_distribution
                )
                self.assertEqual(
                    line.analytic_distribution,
                    {
                        str(self.analytic_account_a.id): 50,
                        str(self.analytic_account_c.id): 50,
                    },
                )
