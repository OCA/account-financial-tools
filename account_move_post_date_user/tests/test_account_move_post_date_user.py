# Copyright 2024 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMovePostDateUser(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_move_obj = cls.env["account.move"]
        cls.account = cls.company_data["default_account_revenue"]
        cls.account2 = cls.company_data["default_account_expense"]
        cls.journal = cls.company_data["default_journal_bank"]

        # create a move and post it
        cls.move = cls.account_move_obj.create(
            {
                "date": fields.Date.today(),
                "journal_id": cls.journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": cls.account.id,
                            "credit": 1000.0,
                            "name": "Credit line",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": cls.account2.id,
                            "debit": 1000.0,
                            "name": "Debit line",
                        },
                    ),
                ],
            }
        )

    def test_account_move_post_date_user(self):
        self.move.action_post()
        self.assertEqual(self.move.last_post_date.date(), fields.Date.today())
        self.assertEqual(self.move.last_post_uid, self.env.user)
