# Copyright 2023 David Jaen <david.jaen.revert@gmail.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, TransactionCase


class TestAccountMoveBudget(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.type = cls.env["date.range.type"].create(
            {"name": "Fiscal year", "company_id": False, "allow_overlap": False}
        )

        cls.date_range = cls.env["date.range"].create(
            {
                "name": "FS2023",
                "date_start": "2023-01-01",
                "date_end": "2023-12-31",
                "type_id": cls.type.id,
            }
        )

        cls.date_range2 = cls.env["date.range"].create(
            {
                "name": "FS2024",
                "date_start": "2024-01-01",
                "date_end": "2024-12-31",
                "type_id": cls.type.id,
            }
        )

        user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Because I am budgetman!",
                    "login": "budgetman",
                    "groups_id": [
                        (6, 0, cls.env.user.groups_id.ids),
                        (4, cls.env.ref("account.group_account_user").id),
                    ],
                }
            )
        )
        user.partner_id.email = "budgetman@test.com"
        cls.env = cls.env(user=user)

        cls.account = cls.env["account.account"].create(
            {
                "code": "TT",
                "name": "Test Account",
                "account_type": "asset_fixed",
            }
        )

    def test_01_create_account_move_budget(self):
        move_form = Form(self.env["account.move.budget"])
        move_form.name = "Budget Test 01"
        move_form.description = "Description"
        move_form.date_range_id = self.date_range
        move_budget = move_form.save()

        move_line_form = Form(self.env["account.move.budget.line"])
        move_line_form.name = "Dummy line"
        move_line_form.budget_id = move_budget
        move_line_form.date = "2023-01-02"
        move_line_form.partner_id = self.env.user.partner_id
        move_line_form.credit = 3000
        move_line_form.debit = 5000
        move_line_form.account_id = self.account
        move_line_form.save()

    def test_02_change_date_range_account_move_budget(self):
        move_form = Form(self.env["account.move.budget"])
        move_form.name = "Budget Test 02"
        move_form.description = "Description"
        move_form.date_range_id = self.date_range
        move_form.state = "draft"
        move_form.date_range_id = self.date_range2
        self.assertTrue(move_form.save())

    def test_03_copy_account_move_budget(self):
        move_form = Form(self.env["account.move.budget"])
        move_form.name = "Budget Test 03"
        move_form.description = "Description"
        move_form.date_range_id = self.date_range
        move_form.state = "draft"
        self.assertTrue(move_form.save().copy())

    def test_04_actions_account_move_budget(self):
        values = {
            "name": "Budget Test 04",
            "description": "Description",
            "date_range_id": self.date_range.id,
            "date_from": self.date_range.date_start,
            "date_to": self.date_range.date_end,
        }
        budget = self.env["account.move.budget"].create(values)

        budget.action_draft()
        self.assertTrue(budget.state == "draft")
        budget.action_cancel()
        self.assertTrue(budget.state == "cancelled")
        budget.action_confirm()
        self.assertTrue(budget.state == "confirmed")

    def test_05_raise_account_move_budget(self):
        move_form = Form(self.env["account.move.budget"])
        move_form.name = "Budget Test 05"
        move_form.description = "Description"
        move_form.date_range_id = self.date_range
        move_form.date_from = "2021-01-01"
        move_form.save()

    def test_06_raise_account_move_budget(self):
        values = {
            "name": "Budget Test 06",
            "description": "Description",
            "date_range_id": self.date_range.id,
            "date_from": "2023-02-01",
            "date_to": "2023-12-30",
        }
        move_budget = self.env["account.move.budget"].create(values)

        move_line_form = Form(self.env["account.move.budget.line"])
        move_line_form.name = "Dummy line"
        move_line_form.budget_id = move_budget
        move_line_form.date = "2021-01-02"
        move_line_form.partner_id = self.env.user.partner_id
        move_line_form.credit = 3000
        move_line_form.debit = 5000
        move_line_form.account_id = self.account
        with self.assertRaises(ValidationError):
            move_line_form.save()
