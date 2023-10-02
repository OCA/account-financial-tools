# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests import common


class TestAccountJournalRestrictMode(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountJournalRestrictMode, cls).setUpClass()
        cls.account_journal_obj = cls.env["account.journal"]

    def test_journal_default_lock_entries(self):
        journal = self.account_journal_obj.create(
            {"name": "Test Journal", "code": "TJ", "type": "general"}
        )
        self.assertTrue(journal.restrict_mode_hash_table)
        with self.assertRaises(UserError):
            journal.write({"restrict_mode_hash_table": False})
