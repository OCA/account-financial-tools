# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAccountMoveTotalsByAccountType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_model = cls.env["account.account"]
        cls.company = cls.env.ref("base.main_company")
        # Create account for Goods Received Not Invoiced
        name = "Goods Received Not Invoiced"
        code = "grni"
        cls.account_grni = cls._create_account(cls, "liability_payable", name, code)

        # Create account for Cost of Goods Sold
        name = "Cost of Goods Sold"
        code = "cogs"
        cls.account_cogs = cls._create_account(cls, "expense", name, code)
        # Create account for Inventory
        name = "Inventory"
        code = "inventory"
        cls.account_inventory = cls._create_account(cls, "asset_fixed", name, code)
        # Create Income account
        # Create account for Inventory
        name = "Income"
        code = "income"
        cls.account_income = cls._create_account(cls, "income", name, code)
        cls.journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.env.user.company_id.id)], limit=1
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

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

    def _create_account(self, acc_type, name, code):
        """Create an account."""
        account = self.account_model.create(
            {
                "name": name,
                "code": code,
                "account_type": acc_type,
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
