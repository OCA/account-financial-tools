# Copyright 2024 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMovePostDateUser(AccountTestInvoicingCommon):
    def setUp(self):
        super().setUp()
        self.account_move_obj = self.env["account.move"]
        self.partner = self.browse_ref("base.res_partner_12")
        self.account = self.company_data["default_account_revenue"]
        self.account2 = self.company_data["default_account_expense"]
        self.journal = self.company_data["default_journal_bank"]

        # create a move and post it
        self.move = self.account_move_obj.create(
            {
                "date": fields.Date.today(),
                "journal_id": self.journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account.id,
                            "credit": 1000.0,
                            "name": "Credit line",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account2.id,
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
