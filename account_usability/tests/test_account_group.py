from odoo.tests.common import TransactionCase


class AccountGroupTest(TransactionCase):
    def test_group_accounts(self):
        group = self.env["account.group"].create(
            {
                "name": "Test Group",
                "code_prefix_start": "1000",
                "code_prefix_end": "1999",
            }
        )

        account = self.env["account.account"].create(
            {"code": "1001", "name": "Test Account"}
        )
        account_2 = self.env["account.account"].create(
            {"code": "2000", "name": "Test Account"}
        )

        self.assertIn(account.id, group.account_ids.ids)
        self.assertNotIn(account_2.id, group.account_ids.ids)

        account_3 = self.env["account.account"].create(
            {"code": "1002", "name": "Test Account 2"}
        )
        self.assertIn(account_3.id, group.account_ids.ids)

        account_3.write({"code": "2001"})
        self.assertNotIn(account_3.id, group.account_ids.ids)
        self.assertIn(account.id, group.account_ids.ids)

    def test_search_accounts_on_group(self):
        group = self.env["account.group"].create(
            {
                "name": "Test Group",
                "code_prefix_start": "1000",
                "code_prefix_end": "1999",
            }
        )

        account = self.env["account.account"].create(
            {"code": "1001", "name": "Test Account"}
        )
        account_2 = self.env["account.account"].create(
            {"code": "2000", "name": "Test Account"}
        )

        accounts_by_group = self.env["account.account"].search(
            [("group_id", "=", group.id)]
        )

        self.assertIn(account.id, accounts_by_group.ids)
        self.assertNotIn(account_2.id, accounts_by_group.ids)

        account_3 = self.env["account.account"].create(
            {"code": "1002", "name": "Test Account 2"}
        )
        accounts_by_group = self.env["account.account"].search(
            [("group_id", "=", group.id)]
        )
        self.assertIn(account_3.id, accounts_by_group.ids)
        self.assertIn(account.id, accounts_by_group.ids)
        self.assertNotIn(account_2.id, accounts_by_group.ids)

        accounts_by_group = self.env["account.account"].search(
            [("group_id.code_prefix_start", "=", "1000")]
        )
        self.assertIn(account_3.id, accounts_by_group.ids)
        self.assertNotIn(account_2.id, accounts_by_group.ids)
        self.assertIn(account.id, accounts_by_group.ids)
