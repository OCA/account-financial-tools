from odoo import Command
from odoo.tests import TransactionCase


class TestAccountUsability(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tag = cls.env["account.account.tag"].create(
            {"name": "Test Tag", "applicability": "accounts"}
        )
        cls.account_1 = cls.env["account.account"].create(
            {"name": "Test Account 1", "code": "1001"}
        )
        cls.account_2 = cls.env["account.account"].create(
            {"name": "Test Account 2", "code": "2000"}
        )

    def test_search_accounts_on_tag(self):
        # The m2o follows the core account_ids <-> tag_ids m2m.
        self.account_1.tag_ids = [Command.set(self.tag.ids)]
        self.assertEqual(self.account_1.tag_id, self.tag)

        accounts = self.env["account.account"].search([("tag_id", "=", self.tag.id)])
        self.assertEqual(accounts, self.account_1)

        # Dotted search through the m2o, like the account group search
        # this module provided before Odoo 20.0.
        accounts = self.env["account.account"].search(
            [("tag_id.name", "=", "Test Tag")]
        )
        self.assertEqual(accounts, self.account_1)

        # Removing the tag from the core m2m clears the m2o too.
        self.account_1.tag_ids = [Command.clear()]
        accounts = self.env["account.account"].search([("tag_id", "=", self.tag.id)])
        self.assertFalse(accounts)

    def test_tag_id_follows_tag_side(self):
        # Linking the account from the tag form (account_ids) must update
        # the m2o as well.
        self.tag.account_ids = [Command.link(self.account_2.id)]
        self.assertEqual(self.account_2.tag_id, self.tag)
        accounts = self.env["account.account"].search([("tag_id", "=", self.tag.id)])
        self.assertEqual(accounts, self.account_2)
