# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.account_reversal_usability.models.account_move import (
    MoveAlreadyReversedValidationError,
)


@tagged("post_install", "-at_install")
class TestAccountMoveReversal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.account = cls.env["account.account"].create(
            {
                "name": "ACCOUNT",
                "code": "MYTESTACCOUNT",
                "account_type": "asset_receivable",
                "company_id": cls.company.id,
            }
        )
        cls.AccountMove = cls.env["account.move"]

    def test_account_move_reversal(self):
        account_move = self.AccountMove.create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2016-01-01"),
                "line_ids": [
                    Command.create(
                        {
                            "display_type": "payment_term",
                            "account_id": self.account.id,
                            "debit": 100.0,
                            "credit": 0.0,
                            "amount_currency": 200.0,
                        }
                    ),
                    Command.create(
                        {
                            "display_type": "payment_term",
                            "account_id": self.account.id,
                            "debit": 0.0,
                            "credit": 100.0,
                            "amount_currency": -200.0,
                        }
                    ),
                ],
            }
        )
        account_move.action_post()
        account_move.to_be_reversed = True
        reversed_account_move = account_move._reverse_moves()
        self.assertEqual(account_move.reversal_id, reversed_account_move)
        self.assertFalse(account_move.to_be_reversed)
        with self.assertRaises(MoveAlreadyReversedValidationError), self.cr.savepoint():
            account_move.to_be_reversed = True
