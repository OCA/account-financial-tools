# Copyright 2022 Acsone SA (http://www.acsone.eu/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase


class TestAccountAccount(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.misc_journal = cls.env["account.journal"].create(
            {
                "name": "Test Journal Move name seq",
                "code": "ADLM",
                "type": "general",
                "company_id": cls.env.company.id,
            }
        )
        cls.accounts = cls.env["account.account"].search(
            [("company_id", "=", cls.env.company.id)], limit=2
        )
        cls.account1 = cls.accounts[0]
        cls.account2 = cls.accounts[1]
        cls.date = fields.Datetime.now()

    def test_constraint_code(self):

        self.account1.write({"code": 123456})
        move = self.env["account.move"].create(
            {
                "date": self.date,
                "journal_id": self.misc_journal.id,
                "line_ids": [
                    (0, 0, {"account_id": self.account1.id, "debit": 10}),
                    (0, 0, {"account_id": self.account2.id, "credit": 10}),
                ],
            }
        )
        with self.assertRaises(ValidationError) as ve:
            self.account1.write({"code": 123789})
        self.assertIn(
            "You cannot change the code of account which contains journal items.",
            ve.exception.args[0],
        )
        move.action_post()
        with self.assertRaises(ValidationError) as ve:
            self.account1.write({"code": 654321})
        self.assertIn(
            "You cannot change the code of account which contains journal items.",
            ve.exception.args[0],
        )
