# Copyright 2020 Ecosoft (http://ecosoft.co.th)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, TransactionCase


class TestAccountMoveTemplateEnhanced(TransactionCase):
    def setUp(self):
        super(TestAccountMoveTemplateEnhanced, self).setUp()
        self.Move = self.env["account.move"]
        self.Journal = self.env["account.journal"]
        self.Account = self.env["account.account"]
        self.Template = self.env["account.move.template"]
        self.Partner = self.env["res.partner"]

        self.journal = self.Journal.search([("type", "=", "general")], limit=1)
        self.ar_account_id = self.Account.search(
            [("user_type_id.type", "=", "receivable")], limit=1
        )
        self.ap_account_id = self.Account.search(
            [("user_type_id.type", "=", "payable")], limit=1
        )
        self.income_account_id = self.Account.search(
            [
                ("user_type_id.type", "=", "other"),
                ("user_type_id.internal_group", "=", "income"),
            ],
            limit=1,
        )
        self.expense_account_id = self.Account.search(
            [
                ("user_type_id.type", "=", "other"),
                ("user_type_id.internal_group", "=", "expense"),
            ],
            limit=1,
        )
        self.partners = self.Partner.search([], limit=3)

        # Create a simple move tempalte
        ar_line = {
            "sequence": 0,
            "name": "AR Line 1",
            "account_id": self.ar_account_id.id,
            "opt_account_id": self.ap_account_id.id,
            "move_line_type": "dr",
            "type": "input",
        }
        income_line1 = {
            "sequence": 1,
            "name": "Income Line 2",
            "account_id": self.income_account_id.id,
            "opt_account_id": self.expense_account_id.id,
            "move_line_type": "cr",
            "type": "computed",
            "python_code": "L0*1/3",
        }
        income_line2 = {
            "sequence": 2,
            "name": "Income Line 2",
            "account_id": self.income_account_id.id,
            "opt_account_id": self.expense_account_id.id,
            "move_line_type": "cr",
            "type": "computed",
            "python_code": "L0*2/3",
        }

        self.move_template = self.Template.create(
            {
                "name": "Test Template",
                "journal_id": self.journal.id,
                "line_ids": [
                    (0, 0, ar_line),
                    (0, 0, income_line1),
                    (0, 0, income_line2),
                ],
            }
        )

    def test_move_template_normal(self):
        """Test normal case, input amount 300"""
        with Form(self.env["account.move.template.run"]) as f:
            f.template_id = self.move_template
        template_run = f.save()
        template_run.load_lines()
        template_run.line_ids[0].amount = 300
        res = template_run.generate_move()
        move = self.Move.browse(res["res_id"])
        self.assertRecordValues(
            move.line_ids.sorted("credit"),
            [
                {"account_id": self.ar_account_id.id, "credit": 0.0, "debit": 300.0},
                {
                    "account_id": self.income_account_id.id,
                    "credit": 100.0,
                    "debit": 0.0,
                },
                {
                    "account_id": self.income_account_id.id,
                    "credit": 200.0,
                    "debit": 0.0,
                },
            ],
        )

    def test_move_template_optional(self):
        """Test optional case, input amount -300, expect optional account"""
        with Form(self.env["account.move.template.run"]) as f:
            f.template_id = self.move_template
        template_run = f.save()
        template_run.load_lines()
        template_run.line_ids[0].amount = -300  # Negative amount
        res = template_run.generate_move()
        move = self.Move.browse(res["res_id"])
        self.assertRecordValues(
            move.line_ids.sorted("debit"),
            [
                {"account_id": self.ap_account_id.id, "credit": 300.0, "debit": 0.0},
                {
                    "account_id": self.expense_account_id.id,
                    "credit": 0.0,
                    "debit": 100.0,
                },
                {
                    "account_id": self.expense_account_id.id,
                    "credit": 0.0,
                    "debit": 200.0,
                },
            ],
        )

    def test_move_template_overwrite(self):
        """Test case overwrite, amount = 3000, no need to manual input"""
        # Test for error when debit is not a valid field
        with Form(self.env["account.move.template.run"]) as f:
            f.template_id = self.move_template
            f.overwrite = str(
                {
                    "L0": {
                        "partner_id": self.partners[0].id,
                        "amount": 3000,
                        "debit": 3000,
                    },
                }
            )
        template_run = f.save()
        with self.assertRaises(ValidationError):
            template_run.load_lines()
        # Assign only on valid fields, and load_lines again
        with Form(self.env["account.move.template.run"]) as f:
            f.template_id = self.move_template
            f.overwrite = str(
                {
                    "L0": {"partner_id": self.partners[0].id, "amount": 3000},
                    "L1": {"partner_id": self.partners[1].id},
                    "L2": {"partner_id": self.partners[2].id},
                }
            )
        template_run = f.save()
        res = template_run.load_lines()
        self.assertEqual(template_run.line_ids[0].partner_id, self.partners[0])
        self.assertEqual(template_run.line_ids[0].amount, 3000)
        res = template_run.with_context(res["context"]).generate_move()
        move = self.Move.browse(res["res_id"])
        self.assertRecordValues(
            move.line_ids.sorted("credit"),
            [
                {
                    "partner_id": self.partners[0].id,
                    "account_id": self.ar_account_id.id,
                    "credit": 0.0,
                    "debit": 3000.0,
                },
                {
                    "partner_id": self.partners[1].id,
                    "account_id": self.income_account_id.id,
                    "credit": 1000.0,
                    "debit": 0.0,
                },
                {
                    "partner_id": self.partners[2].id,
                    "account_id": self.income_account_id.id,
                    "credit": 2000.0,
                    "debit": 0.0,
                },
            ],
        )
