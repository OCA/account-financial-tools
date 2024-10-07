# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAccountLoanAnalyticAccount(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.company_02 = cls.env["res.company"].create({"name": "Auxiliar company"})
        cls.journal = cls.env["account.journal"].create(
            {
                "company_id": cls.company.id,
                "type": "purchase",
                "name": "Debts",
                "code": "DBT",
            }
        )
        cls.loan_account = cls.create_account(
            "DEP",
            "depreciation",
            "liability_current",
        )
        cls.payable_account = cls.create_account("PAY", "payable", "liability_payable")
        cls.asset_account = cls.create_account("ASSET", "asset", "liability_payable")
        cls.interests_account = cls.create_account("FEE", "Fees", "expense")
        cls.lt_loan_account = cls.create_account(
            "LTD",
            "Long term depreciation",
            "liability_non_current",
        )
        cls.partner = cls.env["res.partner"].create({"name": "Bank"})
        cls.product = cls.env["product.product"].create(
            {"name": "Payment", "type": "service"}
        )
        cls.interests_product = cls.env["product.product"].create(
            {"name": "Bank fee", "type": "service"}
        )
        cls.env.user.groups_id += cls.env.ref("analytic.group_analytic_accounting")

        cls.default_plan = cls.env["account.analytic.plan"].create(
            {"name": "Default", "company_id": False}
        )
        cls.analytic_account_a = cls.env["account.analytic.account"].create(
            {
                "name": "analytic_account_a",
                "plan_id": cls.default_plan.id,
                "company_id": False,
            }
        )
        cls.analytic_account_b = cls.env["account.analytic.account"].create(
            {
                "name": "analytic_account_b",
                "plan_id": cls.default_plan.id,
                "company_id": False,
            }
        )
        cls.analytic_account_c = cls.env["account.analytic.account"].create(
            {
                "name": "analytic_account_c",
                "plan_id": cls.default_plan.id,
                "company_id": False,
            }
        )

        cls.loan = cls.create_loan("fixed-annuity", 500000, 1, 60)

    @classmethod
    def create_account(cls, code, name, account_type):
        return cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "name": name,
                "code": code,
                "account_type": account_type,
                "reconcile": True,
            }
        )

    @classmethod
    def create_loan(cls, type_loan, amount, rate, periods):
        loan = cls.env["account.loan"].create(
            {
                "journal_id": cls.journal.id,
                "rate_type": "napr",
                "loan_type": type_loan,
                "loan_amount": amount,
                "payment_on_first_period": True,
                "rate": rate,
                "periods": periods,
                "leased_asset_account_id": cls.asset_account.id,
                "short_term_loan_account_id": cls.loan_account.id,
                "interest_expenses_account_id": cls.interests_account.id,
                "product_id": cls.product.id,
                "interests_product_id": cls.interests_product.id,
                "partner_id": cls.partner.id,
                "analytic_distribution": {
                    cls.analytic_account_a.id: 50,
                    cls.analytic_account_b.id: 50,
                },
            }
        )
        loan.compute_lines()
        return loan

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
