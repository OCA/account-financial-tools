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

    def test_search_group_id_parent_child_overlap(self):
        """Accounts must appear in their most specific group only.

        When a parent group has a broad prefix range and a child group
        has a more specific prefix within that range, searching by the
        parent group_id must NOT return accounts that belong to the
        child group. This prevents duplicate rows in financial reports
        like MIS Builder.
        """
        parent_group = self.env["account.group"].create(
            {
                "name": "Parent Group",
                "code_prefix_start": "9840",
                "code_prefix_end": "9849",
            }
        )
        child_group = self.env["account.group"].create(
            {
                "name": "Child Group",
                "code_prefix_start": "98410",
                "code_prefix_end": "98419",
            }
        )
        account_child = self.env["account.account"].create(
            {"code": "98410", "name": "Account in Child Range"}
        )
        account_parent = self.env["account.account"].create(
            {"code": "98400", "name": "Account in Parent Range Only"}
        )
        account_outside = self.env["account.account"].create(
            {"code": "98500", "name": "Account Outside"}
        )

        child_accounts = self.env["account.account"].search(
            [("group_id", "=", child_group.id)]
        )
        self.assertIn(account_child.id, child_accounts.ids)
        self.assertNotIn(account_parent.id, child_accounts.ids)
        self.assertNotIn(account_outside.id, child_accounts.ids)

        parent_accounts = self.env["account.account"].search(
            [("group_id", "=", parent_group.id)]
        )
        self.assertIn(account_parent.id, parent_accounts.ids)
        self.assertNotIn(
            account_child.id,
            parent_accounts.ids,
            "Account in child group range must not appear in parent group search",
        )
        self.assertNotIn(account_outside.id, parent_accounts.ids)

        parent_via_path = self.env["account.account"].search(
            [("group_id.code_prefix_start", "=", "9840")]
        )
        self.assertIn(account_parent.id, parent_via_path.ids)
        self.assertNotIn(
            account_child.id,
            parent_via_path.ids,
            "Dotted path search must also respect most-specific group",
        )
