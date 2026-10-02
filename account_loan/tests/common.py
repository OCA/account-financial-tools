# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import Command
from odoo.exceptions import UserError

from odoo.addons.base.tests.common import BaseCommon


class LoanCommon(BaseCommon):
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
        cls.general_journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "general")], limit=1
        )
        cls.general_journal.restrict_mode_hash_table = False
        cls.loan_account = cls.create_account(
            "DEP",
            "depreciation",
            "liability_current",
        )
        cls.payable_account = cls.create_account("PAY", "payable", "liability_payable")
        cls.interests_account = cls.create_account("FEE", "Fees", "expense")
        cls.lt_loan_account = cls.create_account(
            "LTD",
            "Long term depreciation",
            "liability_non_current",
        )
        cls.partner = cls.env["res.partner"].create({"name": "Bank"})

    def post(self, loan):
        self.assertFalse(loan.move_ids)
        post = (
            self.env["account.loan.post"]
            .with_context(default_loan_id=loan.id)
            .create({})
        )
        post.run()
        self.assertTrue(loan.move_ids)
        with self.assertRaises(UserError):
            post.run()

    @classmethod
    def create_account(cls, code, name, account_type):
        return cls.env["account.account"].create(
            {
                "company_ids": [Command.set([cls.company.id])],
                "name": name,
                "code": code,
                "account_type": account_type,
                "reconcile": True,
            }
        )

    def _prepare_loan_data(
        self,
        loan_method,
        amount,
        rate,
        periods,
        loan_type="loan",
        journal=None,
        partner=None,
    ):
        if not journal:
            if loan_type in ("loan", "borrow"):
                journal = self.general_journal
            else:
                journal = self.journal

        return {
            "journal_id": journal.id,
            "rate_type": "napr",
            "loan_type": loan_type,
            "loan_method": loan_method,
            "loan_amount": amount,
            "payment_on_first_period": True,
            "rate": rate,
            "periods": periods,
            "short_term_loan_account_id": self.loan_account.id,
            "interest_expenses_account_id": self.interests_account.id,
            "partner_id": partner.id if partner else self.partner.id,
        }

    def create_loan(
        self, loan_method, amount, rate, periods, compute_lines=True, **kawargs
    ):
        loan_values = self._prepare_loan_data(
            loan_method, amount, rate, periods, **kawargs
        )
        loan = self.env["account.loan"].create(loan_values)
        if compute_lines:
            loan.compute_lines()
        return loan
