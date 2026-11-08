# Copyright 2025 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)


from odoo.fields import Command
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMoveGroupRestriction(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.group_account_user = cls.env.ref("account.group_account_user")
        cls.group_restricted_account_management = cls.env.ref(
            "account_move_group_restriction.group_restricted_account_management"
        )
        Users = cls.env["res.users"].with_context(no_reset_password=True)
        cls.user_basic = Users.create(
            {
                "name": "Basic Accounting User",
                "login": "basic_account_user",
                "email": "basic@example.com",
                "company_id": cls.company.id,
                "company_ids": [Command.set([cls.company.id])],
                "group_ids": [Command.set([cls.group_account_user.id])],
            }
        )
        cls.user_management = Users.create(
            {
                "name": "Accounting Management User",
                "login": "management_account_user",
                "email": "management@example.com",
                "company_id": cls.company.id,
                "company_ids": [Command.set([cls.company.id])],
                "group_ids": [
                    Command.set([cls.group_restricted_account_management.id])
                ],
            }
        )
        cls.account_public = cls.env["account.account"].create(
            {
                "name": "Public Account",
                "code": "PUB001",
                "account_type": "asset_current",
                "company_ids": [Command.set([cls.company.id])],
            }
        )
        cls.account_restricted = cls.env["account.account"].create(
            {
                "name": "Restricted Account",
                "code": "RES001",
                "account_type": "asset_current",
                "company_ids": [Command.set([cls.company.id])],
                "security_group_ids": [
                    Command.set([cls.group_restricted_account_management.id])
                ],
            }
        )
        cls.purchase_journal = cls.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.ref_public = "REF-PUB-001"
        cls.ref_restricted = "REF-RES-001"
        cls.ref_mixed = "REF-MIXED-001"
        # Unique amounts per bill so core's case-2 duplicate scan
        # ("same partner + amount + date") doesn't match across fixtures.
        cls.bill_public = cls._create_bill([(cls.account_public, 100)], cls.ref_public)
        cls.bill_restricted = cls._create_bill(
            [(cls.account_restricted, 200)], cls.ref_restricted
        )
        cls.bill_mixed = cls._create_bill(
            [(cls.account_public, 100), (cls.account_restricted, 200)],
            cls.ref_mixed,
        )

    @classmethod
    def _create_bill(cls, lines, ref, user=None):
        Move = cls.env["account.move"]
        if user is not None:
            Move = Move.with_user(user)
        return Move.create(
            {
                "move_type": "in_invoice",
                "partner_id": cls.vendor.id,
                "journal_id": cls.purchase_journal.id,
                "invoice_date": "2026-01-01",
                "ref": ref,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": f"Line {i}",
                            "account_id": account.id,
                            "quantity": 1,
                            "price_unit": price,
                            "tax_ids": [Command.clear()],
                        }
                    )
                    for i, (account, price) in enumerate(lines, 1)
                ],
            }
        )

    def test_account_security_group_ids_computed_from_accounts(self):
        self.assertFalse(self.bill_public.account_security_group_ids)
        self.assertEqual(
            self.bill_restricted.account_security_group_ids,
            self.group_restricted_account_management,
        )
        self.assertEqual(
            self.bill_mixed.account_security_group_ids,
            self.group_restricted_account_management,
        )

    def test_basic_user_cannot_see_restricted_moves(self):
        Move_basic = self.env["account.move"].with_user(self.user_basic)
        public = Move_basic.search([("id", "=", self.bill_public.id)])
        restricted = Move_basic.search([("id", "=", self.bill_restricted.id)])
        mixed = Move_basic.search([("id", "=", self.bill_mixed.id)])
        self.assertEqual(public, self.bill_public, "Basic user should see public bill.")
        self.assertFalse(restricted, "Basic user should not see restricted bill.")
        self.assertFalse(
            mixed, "Basic user should not see bill using restricted account."
        )

    def test_management_user_can_see_all_moves(self):
        Move_mgmt = self.env["account.move"].with_user(self.user_management)
        for bill in (self.bill_public, self.bill_restricted, self.bill_mixed):
            result = Move_mgmt.search([("id", "=", bill.id)])
            self.assertEqual(
                result, bill, f"Management user should see bill {bill.id}."
            )

    def test_basic_user_cannot_see_restricted_move_lines(self):
        Line_basic = self.env["account.move.line"].with_user(self.user_basic)
        public_lines = Line_basic.search([("move_id", "=", self.bill_public.id)])
        restricted_lines = Line_basic.search(
            [("move_id", "=", self.bill_restricted.id)]
        )
        mixed_lines = Line_basic.search([("move_id", "=", self.bill_mixed.id)])
        self.assertTrue(public_lines, "Basic user should see lines of public bill.")
        self.assertFalse(
            restricted_lines,
            "Basic user should not see lines of restricted bill.",
        )
        self.assertFalse(
            mixed_lines,
            "Basic user should not see lines of bill using restricted account.",
        )

    def test_management_user_can_see_all_move_lines(self):
        Line_mgmt = self.env["account.move.line"].with_user(self.user_management)
        for bill in (self.bill_public, self.bill_restricted, self.bill_mixed):
            lines = Line_mgmt.search([("move_id", "=", bill.id)])
            self.assertTrue(
                lines, f"Management user should see lines of bill {bill.id}."
            )

    def test_basic_user_duplicate_ref_does_not_leak(self):
        """A basic user creating a bill that duplicates a restricted bill
        must not see the restricted bill exposed via `duplicated_ref_ids`."""
        bill = self._create_bill(
            [(self.account_public, 200)],
            self.ref_restricted,
            user=self.user_basic,
        )
        self.assertFalse(
            bill.duplicated_ref_ids,
            "Restricted duplicate must not be exposed via duplicated_ref_ids.",
        )

    def test_management_user_sees_duplicate_directly(self):
        """A user who can read the restricted bill sees it via
        `duplicated_ref_ids`."""
        bill = self._create_bill(
            [(self.account_public, 200)],
            self.ref_restricted,
            user=self.user_management,
        )
        self.assertEqual(
            bill.duplicated_ref_ids,
            self.bill_restricted,
            "Management user should see the restricted bill as a duplicate.",
        )
