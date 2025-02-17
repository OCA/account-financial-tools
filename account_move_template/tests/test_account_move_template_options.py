# Copyright 2020 Ecosoft (http://ecosoft.co.th)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMoveTemplateEnhanced(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.company_data["company"]
        cls.env.user.write({"company_ids": [Command.link(cls.company.id)]})
        cls.Move = cls.env["account.move"]
        cls.Journal = cls.env["account.journal"]
        cls.Account = cls.env["account.account"]
        cls.Template = cls.env["account.move.template"]
        cls.Partner = cls.env["res.partner"]

        cls.journal = cls.company_data["default_journal_misc"]
        cls.ar_account_id = cls.company_data["default_account_receivable"]
        cls.ap_account_id = cls.company_data["default_account_payable"]
        cls.income_account_id = cls.company_data["default_account_revenue"]
        cls.expense_account_id = cls.company_data["default_account_expense"]
        cls.automatic_balancing_account_id = cls._get_first_record(
            cls.Account, [("code", "=", "101402")]
        )
        cls.tax_paid_account_id = cls._get_first_record(
            cls.Account, [("code", "=", "131000")]
        )

        cls.partner0 = cls.Partner.create({"name": "Beloved test partner"})
        cls.partner1 = cls.Partner.create({"name": "World company test inc."})
        cls.partner2 = cls.Partner.create({"name": "Odoo debug expert GmbH"})

        cls.payment_term = cls._get_first_record(
            cls.env["account.payment.term.line"], [("nb_days", "=", 30)]
        )
        cls.tax = cls._get_first_record(
            cls.env["account.tax"],
            [("type_tax_use", "=", "purchase"), ("company_id", "=", cls.company.id)],
        )

        cls.move_template = cls._create_move_template("Test Template", with_tax=False)
        cls.move_template_with_tax_and_payment_terms = cls._create_move_template(
            "Test Template With Tax And Payment Terms", with_tax=True
        )

    @classmethod
    def _get_first_record(cls, model, domain):
        return model.search(domain, limit=1)

    @classmethod
    def _create_move_template(cls, name, with_tax=False):
        ar_line = {
            "sequence": 0,
            "name": "AR Line 1" + (" With Tax And Payment Terms" if with_tax else ""),
            "account_id": cls.ar_account_id.id,
            "opt_account_id": cls.ap_account_id.id,
            "move_line_type": "dr",
            "type": "input",
        }
        if with_tax:
            ar_line.update(
                {"payment_term_id": cls.payment_term.id, "tax_ids": cls.tax.ids}
            )

        income_line1 = {
            "sequence": 1,
            "name": "Income Line 1",
            "account_id": cls.income_account_id.id,
            "opt_account_id": cls.expense_account_id.id,
            "move_line_type": "cr",
            "type": "computed",
            "python_code": "L0*1/3",
        }
        income_line2 = {
            "sequence": 2,
            "name": "Income Line 2",
            "account_id": cls.income_account_id.id,
            "opt_account_id": cls.expense_account_id.id,
            "move_line_type": "cr",
            "type": "computed",
            "python_code": "L0*2/3",
        }

        return cls.Template.create(
            {
                "name": name,
                "journal_id": cls.journal.id,
                "company_id": cls.company.id,
                "line_ids": [
                    Command.create(ar_line),
                    Command.create(income_line1),
                    Command.create(income_line2),
                ],
            }
        )

    def _run_template_and_validate(
        self, template, input_amount, expected_values, sort_field
    ):
        wiz = self.env["account.move.template.run"].create({"template_id": template.id})
        wiz.load_lines()
        wiz.line_ids[0].amount = input_amount
        res = wiz.generate_move()
        move = self.Move.browse(res["res_id"])
        self.assertRecordValues(move.line_ids.sorted(sort_field), expected_values)

    def test_move_template_normal(self):
        """Test normal case, input amount 300"""
        expected_values = [
            {"account_id": self.ar_account_id.id, "credit": 0.0, "debit": 300.0},
            {"account_id": self.income_account_id.id, "credit": 100.0, "debit": 0.0},
            {"account_id": self.income_account_id.id, "credit": 200.0, "debit": 0.0},
        ]
        self._run_template_and_validate(
            self.move_template, 300, expected_values, "credit"
        )

    def test_move_template_normal_with_tax_and_payment_terms(self):
        """Test case with tax and payment terms, input amount 300"""
        expected_maturity_date = fields.Date.today() + timedelta(days=30)
        expected_values = [
            {
                "account_id": self.ar_account_id.id,
                "credit": 0.0,
                "debit": 300.0,
                "date_maturity": expected_maturity_date,
            },
            {
                "account_id": self.tax_paid_account_id.id,
                "credit": 0.0,
                "debit": 45.0,
                "date_maturity": None,
            },
            {
                "account_id": self.automatic_balancing_account_id.id,
                "credit": 45.0,
                "debit": 0.0,
                "date_maturity": None,
            },
            {
                "account_id": self.income_account_id.id,
                "credit": 100.0,
                "debit": 0.0,
                "date_maturity": fields.Date.today(),
            },
            {
                "account_id": self.income_account_id.id,
                "credit": 200.0,
                "debit": 0.0,
                "date_maturity": fields.Date.today(),
            },
        ]
        self._run_template_and_validate(
            self.move_template_with_tax_and_payment_terms,
            300,
            expected_values,
            "credit",
        )

    def test_move_template_optional(self):
        """Test optional case, input amount -300, expect optional account"""
        expected_values = [
            {"account_id": self.ap_account_id.id, "credit": 300.0, "debit": 0.0},
            {"account_id": self.expense_account_id.id, "credit": 0.0, "debit": 100.0},
            {"account_id": self.expense_account_id.id, "credit": 0.0, "debit": 200.0},
        ]
        self._run_template_and_validate(
            self.move_template, -300, expected_values, "debit"
        )

    def test_move_template_overwrite(self):
        """Test case overwrite, amount = 3000, no need to manual input"""
        # Test for error when debit is not a valid field
        wiz = self.env["account.move.template.run"].create(
            {
                "template_id": self.move_template.id,
                "overwrite": str(
                    {
                        "L0": {
                            "partner_id": self.partner0.id,
                            "amount": 3000,
                            "debit": 3000,
                        },
                    }
                ),
            }
        )
        msg_error = "overwrite are .'partner_id', 'amount', 'name', 'date_maturity'"
        with self.assertRaisesRegex(ValidationError, msg_error):
            wiz.load_lines()
        # Assign only on valid fields, and load_lines again
        wiz = self.env["account.move.template.run"].create(
            {
                "template_id": self.move_template.id,
                "overwrite": str(
                    {
                        "L0": {"partner_id": self.partner0.id, "amount": 3000},
                        "L1": {"partner_id": self.partner1.id},
                        "L2": {"partner_id": self.partner2.id},
                    }
                ),
            }
        )
        res = wiz.load_lines()
        self.assertEqual(wiz.line_ids[0].partner_id, self.partner0)
        self.assertEqual(wiz.line_ids[0].amount, 3000)
        res = wiz.with_context(**res["context"]).generate_move()
        move = self.Move.browse(res["res_id"])
        self.assertRecordValues(
            move.line_ids.sorted("credit"),
            [
                {
                    "partner_id": self.partner0.id,
                    "account_id": self.ar_account_id.id,
                    "credit": 0.0,
                    "debit": 3000.0,
                },
                {
                    "partner_id": self.partner1.id,
                    "account_id": self.income_account_id.id,
                    "credit": 1000.0,
                    "debit": 0.0,
                },
                {
                    "partner_id": self.partner2.id,
                    "account_id": self.income_account_id.id,
                    "credit": 2000.0,
                    "debit": 0.0,
                },
            ],
        )

    def test_move_copy(self):
        template_copy = self.move_template.copy()
        self.assertEqual(template_copy.name, "Test Template (copy)")

    def test_move_generate_from_action_button(self):
        # `Generate Journal Entry` action button
        res = self.move_template.generate_journal_entry()
        self.assertEqual(res["name"], "Create Entry from Template")
        self.assertEqual(res["res_model"], "account.move.template.run")

    def test_move_template_exceptions(self):
        msg_error = "Python Code must be set for computed line with sequence 1."
        with self.assertRaisesRegex(ValidationError, msg_error):
            self.move_template.line_ids[1].python_code = ""

        self.move_template.line_ids[1].python_code = "P0*1/3"
        wiz = self.env["account.move.template.run"].create(
            {
                "template_id": self.move_template.id,
            }
        )
        wiz.load_lines()
        msg_error = "really exists and have a lower sequence than the current line."
        with self.assertRaisesRegex(UserError, msg_error):
            wiz.generate_move()

        self.move_template.line_ids[1].python_code = "L0*"
        wiz = self.env["account.move.template.run"].create(
            {
                "template_id": self.move_template.id,
            }
        )
        wiz.load_lines()
        msg_error = "the syntax of the formula is wrong."
        with self.assertRaisesRegex(UserError, msg_error):
            wiz.generate_move()

        self.move_template.line_ids[1].python_code = "L0*1/3"
        wiz = self.env["account.move.template.run"].create(
            {
                "template_id": self.move_template.id,
            }
        )
        wiz.load_lines()
        wiz.line_ids[0].amount = 0
        msg_error = "Debit and credit of all lines are null."
        with self.assertRaisesRegex(UserError, msg_error):
            wiz.generate_move()

        wiz = self.env["account.move.template.run"].create(
            {
                "template_id": self.move_template.id,
                "overwrite": [],
            }
        )
        msg_error = "Overwrite value must be a valid python dict"
        with self.assertRaisesRegex(ValidationError, msg_error):
            wiz.load_lines()

        wiz = self.env["account.move.template.run"].create(
            {
                "template_id": self.move_template.id,
                "overwrite": str({"P0": {"amount": 100}}),
            }
        )
        msg_error = "Keys must be line sequence i.e. L1, L2, ..."
        with self.assertRaisesRegex(ValidationError, msg_error):
            wiz.load_lines()

        wiz = self.env["account.move.template.run"].create(
            {
                "template_id": self.move_template.id,
                "overwrite": str({"L0": []}),
            }
        )
        msg_error = "Invalid dictionary: 'list' object has no attribute 'keys'"
        with self.assertRaisesRegex(ValidationError, msg_error):
            wiz.load_lines()

        wiz = self.env["account.move.template.run"].create(
            {
                "template_id": self.move_template.id,
                "overwrite": str({"L0": {"test": 100}}),
            }
        )
        msg_error = "overwrite are .'partner_id', 'amount', 'name', 'date_maturity'"
        with self.assertRaisesRegex(ValidationError, msg_error):
            wiz.load_lines()

        wiz = self.env["account.move.template.run"].create(
            {
                "template_id": self.move_template.id,
            }
        )
        wiz.line_ids.unlink()
        msg_error = "You deleted a line in the wizard. This is not allowed:"
        with self.assertRaisesRegex(UserError, msg_error):
            wiz.generate_move()
