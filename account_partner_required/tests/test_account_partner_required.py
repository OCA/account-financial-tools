from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountPartnerRequired(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.account = cls.env["account.account"].create(
            {
                "code": "ACC01",
                "name": "Test Account",
                "account_type": "expense",
            }
        )

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

    def _create_account_move(self, partner, account):
        account = self.env["account.move"].create(
            {
                "partner_id": partner.id if partner else False,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": account.id,
                            "debit": 500.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": account.id,
                            "credit": 500.0,
                        }
                    ),
                ],
            }
        )
        account.action_post()
        return account

    def test_partner_policy_never(self):
        """Partner must NOT be set"""
        self.account.partner_policy = "never"

        with self.assertRaises(ValidationError):
            self._create_account_move(self.partner, self.account)

    def test_partner_policy_always(self):
        """Partner MUST be set"""
        self.account.partner_policy = "always"

        with self.assertRaises(ValidationError):
            self._create_account_move(False, self.account)

    def test_partner_policy_optional(self):
        """Partner is optional (no error expected)"""
        self.account.partner_policy = "optional"

        # With partner
        account_with_partner = self._create_account_move(self.partner, self.account)
        self.assertTrue(account_with_partner)

        # Without partner
        account_without_partner = self._create_account_move(False, self.account)
        self.assertTrue(account_without_partner)
