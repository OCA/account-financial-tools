# Copyright (C) 2025 - Today: Sylvain LE GAL (http://www.grap.coop)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestModule(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountJournal = cls.env["account.journal"]
        cls.AccountAccount = cls.env["account.account"]
        cls.account_cash = cls.AccountAccount.create(
            {
                "code": "CSH99",
                "name": "CSH99 Account",
                "account_type": "asset_cash",
            }
        )

    def test_default_account(self):
        cash_journal = self.AccountJournal.create(
            {
                "code": "AJ-CSH",
                "name": "Journal CSH",
                "type": "cash",
                "default_account_id": self.account_cash.id,
            }
        )
        self.assertEqual(
            cash_journal.outbound_payment_method_line_ids[0].payment_account_id,
            self.account_cash,
        )
        self.assertEqual(
            cash_journal.inbound_payment_method_line_ids[0].payment_account_id,
            self.account_cash,
        )
