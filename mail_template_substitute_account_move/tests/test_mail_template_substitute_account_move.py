# Copyright 2024 Sodexis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestMailTemplateSubstitute(TransactionCase):
    def setUp(self):
        super().setUp()

        self.smt2 = self.env["mail.template"].create(
            {
                "name": "substitute_template_2",
                "model_id": self.env.ref("account.model_account_move").id,
            }
        )

        self.smt1 = self.env["mail.template"].create(
            {
                "name": "substitute_template_1",
                "model_id": self.env.ref("account.model_account_move").id,
                "mail_template_substitution_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "substitution_mail_template_id": self.smt2.id,
                            "domain": "[('id', '=', False)]",
                        },
                    )
                ],
            }
        )

        self.mt = self.env["mail.template"].create(
            {
                "name": "base_template",
                "model_id": self.env.ref("account.model_account_move").id,
                "mail_template_substitution_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "substitution_mail_template_id": self.smt1.id,
                        },
                    )
                ],
            }
        )

        self.move = self.env["account.move"].search(
            [("move_type", "=", "out_invoice")],
            limit=1,
        )

        self.assertTrue(self.move)

    def test_mail_template_substitution(self):
        wizard_model = self.env["account.move.send.wizard"]

        with patch.object(
            type(wizard_model),
            "_get_default_mail_template_id",
            return_value=self.mt,
        ):
            wizard = wizard_model.create(
                {
                    "move_id": self.move.id,
                }
            )

            wizard._compute_mail_template_id()

            self.assertEqual(
                wizard.mail_template_id,
                self.smt1,
                "The mail template should be substituted by the first matching rule.",
            )

    def test_mail_template_without_substitution(self):
        wizard_model = self.env["account.move.send.wizard"]

        with patch.object(
            type(wizard_model),
            "_get_default_mail_template_id",
            return_value=self.smt2,
        ):
            wizard = wizard_model.create(
                {
                    "move_id": self.move.id,
                }
            )

            wizard._compute_mail_template_id()

            self.assertEqual(
                wizard.mail_template_id,
                self.smt2,
                "The original template should be kept when no "
                "substitution rule matches.",
            )
