# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class AccountAccountUsedCommon(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls._create_test_account("999001", "Test account 1")
        cls.other_account = cls._create_test_account("999002", "Test account 2")

    @classmethod
    def _create_test_account(cls, code, name):
        return cls.env["account.account"].create(
            {"code": code, "name": name, "account_type": "income"}
        )

    @classmethod
    def _create_move(cls, account, post=False):
        move = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": cls.company_data["default_journal_misc"].id,
                "line_ids": [
                    Command.create({"account_id": account.id, "credit": 100.0}),
                    Command.create(
                        {
                            "account_id": cls.company_data[
                                "default_account_expense"
                            ].id,
                            "debit": 100.0,
                        }
                    ),
                ],
            }
        )
        if post:
            move.action_post()
        return move
