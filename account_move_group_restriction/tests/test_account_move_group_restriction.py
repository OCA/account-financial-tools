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
                "groups_id": [Command.set([cls.group_account_user.id])],
            }
        )
        cls.user_management = Users.create(
            {
                "name": "Accounting Management User",
                "login": "management_account_user",
                "email": "management@example.com",
                "company_id": cls.company.id,
                "company_ids": [Command.set([cls.company.id])],
                "groups_id": [
                    Command.set([cls.group_restricted_account_management.id])
                ],
            }
        )
        cls.account_public = cls.env["account.account"].create(
            {
                "name": "Public Account",
                "code": "PUB001",
                "account_type": "asset_current",
                "company_id": cls.company.id,
            }
        )
        cls.account_restricted = cls.env["account.account"].create(
            {
                "name": "Restricted Account",
                "code": "RES001",
                "account_type": "asset_current",
                "company_id": cls.company.id,
                "security_group_ids": [
                    Command.set([cls.group_restricted_account_management.id])
                ],
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Miscellaneous",
                "code": "TEST MISC",
                "type": "general",
                "company_id": cls.company.id,
            }
        )
        cls.move_public = cls._create_move(cls.account_public, cls.account_public)
        cls.move_restricted = cls._create_move(
            cls.account_restricted, cls.account_restricted
        )
        cls.move_mixed = cls._create_move(cls.account_restricted, cls.account_public)

    @classmethod
    def _create_move(cls, debit_account, credit_account):
        Move = cls.env["account.move"]
        move = Move.create(
            {
                "move_type": "entry",
                "journal_id": cls.journal.id,
                "company_id": cls.company.id,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Debit line",
                            "account_id": debit_account.id,
                            "debit": 100,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Credit line",
                            "account_id": credit_account.id,
                            "debit": 0.0,
                            "credit": 100,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def test_account_security_group_ids_computed_from_accounts(self):
        self.assertFalse(self.move_public.account_security_group_ids)
        self.assertEqual(
            self.move_restricted.account_security_group_ids,
            self.group_restricted_account_management,
        )
        self.assertEqual(
            self.move_mixed.account_security_group_ids,
            self.group_restricted_account_management,
        )

    def test_basic_user_cannot_see_restricted_moves(self):
        Move_basic = self.env["account.move"].with_user(self.user_basic)
        public_move = Move_basic.search([("id", "=", self.move_public.id)])
        restricted_move = Move_basic.search([("id", "=", self.move_restricted.id)])
        mixed_move = Move_basic.search([("id", "=", self.move_mixed.id)])
        self.assertEqual(
            public_move,
            self.move_public,
            "Basic user should see public move.",
        )
        self.assertFalse(
            restricted_move,
            "Basic user should not see restricted move.",
        )
        self.assertFalse(
            mixed_move,
            "Basic user should not see mixed move using restricted account.",
        )

    def test_management_user_can_see_all_moves(self):
        Move_mgmt = self.env["account.move"].with_user(self.user_management)
        for move in (self.move_public, self.move_restricted, self.move_mixed):
            result = Move_mgmt.search([("id", "=", move.id)])
            self.assertEqual(
                result,
                move,
                "Management user should see move %s." % move.id,
            )

    def test_basic_user_cannot_see_restricted_move_lines(self):
        Line_basic = self.env["account.move.line"].with_user(self.user_basic)
        public_lines = Line_basic.search([("move_id", "=", self.move_public.id)])
        restricted_lines = Line_basic.search(
            [("move_id", "=", self.move_restricted.id)]
        )
        mixed_lines = Line_basic.search([("move_id", "=", self.move_mixed.id)])
        self.assertTrue(
            public_lines,
            "Basic user should see lines of unrestricted move.",
        )
        self.assertFalse(
            restricted_lines,
            "Basic user should not see lines of restricted move.",
        )
        self.assertFalse(
            mixed_lines,
            "Basic user should not see lines of mixed restricted move.",
        )

    def test_management_user_can_see_all_move_lines(self):
        Line_mgmt = self.env["account.move.line"].with_user(self.user_management)
        for move in (self.move_public, self.move_restricted, self.move_mixed):
            lines = Line_mgmt.search([("move_id", "=", move.id)])
            self.assertTrue(
                lines,
                "Management user should see lines of move %s." % move.id,
            )
