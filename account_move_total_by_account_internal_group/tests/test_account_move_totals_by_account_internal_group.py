# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAccountMoveTotalsByAccountType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountMoveTotalsByAccountType, cls).setUpClass()
        cls.account_model = cls.env["account.account"]
        cls.acc_type_model = cls.env["account.account.type"]
        cls.company = cls.env.ref("base.main_company")
        # Create account for Goods Received Not Invoiced
        acc_type = cls._create_account_type(cls, "liability", "other")
        name = "Goods Received Not Invoiced"
        code = "grni"
        cls.account_grni = cls._create_account(cls, acc_type, name, code, cls.company)

        # Create account for Cost of Goods Sold
        acc_type = cls._create_account_type(cls, "expense", "other")
        name = "Cost of Goods Sold"
        code = "cogs"
        cls.account_cogs = cls._create_account(cls, acc_type, name, code, cls.company)
        # Create account for Inventory
        acc_type = cls._create_account_type(cls, "asset", "other")
        name = "Inventory"
        code = "inventory"
        cls.account_inventory = cls._create_account(
            cls, acc_type, name, code, cls.company
        )
        # Create Income account
        # Create account for Inventory
        acc_type = cls._create_account_type(cls, "income", "other")
        name = "Income"
        code = "income"
        cls.account_income = cls._create_account(cls, acc_type, name, code, cls.company)
        cls.journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.env.user.company_id.id)], limit=1
        )
        cls.partner = cls.env.ref("base.res_partner_12")

    def _create_account_move(self, dr_account, cr_account):
        move_vals = {
            "journal_id": self.journal.id,
            "date": "1900-01-01",
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "debit": 100.0,
                        "credit": 0.0,
                        "account_id": dr_account.id,
                        "partner_id": self.partner.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "debit": 0.0,
                        "credit": 100.0,
                        "account_id": cr_account.id,
                        "partner_id": self.partner.id,
                    },
                ),
            ],
        }
        return self.env["account.move"].create(move_vals)

    def _create_account_type(self, name, a_type):
        acc_type = self.acc_type_model.create(
            {"name": name, "type": a_type, "internal_group": name}
        )
        return acc_type

    def _create_account(self, acc_type, name, code, company):
        """Create an account."""
        account = self.account_model.create(
            {
                "name": name,
                "code": code,
                "user_type_id": acc_type.id,
                "company_id": company.id,
                "reconcile": True,
            }
        )
        return account

    def test_01_account_internal_group_balance(self):
        """Create JE with different account types and check the amount total
        by internal group
        """
        account_move = self._create_account_move(
            self.account_inventory, self.account_grni
        )
        self.assertEqual(
            account_move.amount_total_signed_account_internal_group_asset,
            100,
            "Wrong asset",
        )
        self.assertEqual(
            account_move.amount_total_signed_account_internal_group_liability,
            -100,
            "Wrong liability",
        )
        self.assertEqual(
            account_move.amount_total_signed_account_internal_group_expense,
            0,
            "Wrong expense",
        )
        account_move = self._create_account_move(self.account_cogs, self.account_income)
        self.assertEqual(
            account_move.amount_total_signed_account_internal_group_expense,
            100,
            "Wrong Expense",
        )
        self.assertEqual(
            account_move.amount_total_signed_account_internal_group_income,
            -100,
            "Wrong Income",
        )
