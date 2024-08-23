# Copyright 2024 Sodexis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
                    (0, 0, {"substitution_mail_template_id": self.smt1.id})
                ],
            }
        )
        self.mail_compose = self.env["mail.compose.message"].create(
            {"template_id": self.mt.id, "composition_mode": "mass_mail"}
        )
        self.moves = (
            self.env["account.move"]
            .search([])
            .filtered(lambda move: move.is_sale_document(include_receipts=True))
        )
        self.move = self.moves and self.moves[0]

    def test_action_send_and_print(self):
        result = self.move.action_send_and_print()
        self.assertFalse(
            result["context"]["default_mail_template_id"]
            == self.mail_compose.template_id.id
        )
