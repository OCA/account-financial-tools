# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestPartnerCompanyValidation(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.company
        cls.company_b = cls._create_company(name="Company B")
        cls.partner.company_id = cls.company_a
        cls.account = cls.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "TEST.CONST",
                "account_type": "asset_current",
                "company_ids": [Command.set(cls.company_a.ids)],
            }
        )

    def test_01_prevent_company_change_with_moves(self):
        """Test that company change is blocked if moves exist in another company."""
        # Create a move for the partner in Company A
        self.env["account.move"].create(
            {
                "move_type": "entry",
                "partner_id": self.partner.id,
                "company_id": self.company_a.id,
                "line_ids": [
                    Command.create({"name": "line1", "account_id": self.account.id}),
                    Command.create({"name": "line2", "account_id": self.account.id}),
                ],
            }
        )

        # Try to change partner's company to Company B
        with self.assertRaisesRegex(
            ValidationError, "there are journal entries for this partner"
        ):
            self.partner.company_id = self.company_b.id

    def test_02_allow_company_change_without_moves(self):
        """Test that company change is allowed if no moves exist."""
        new_partner = self.env["res.partner"].create(
            {
                "name": "New Partner",
                "company_id": self.company_a.id,
            }
        )
        new_partner.company_id = self.company_b.id
        self.assertEqual(new_partner.company_id, self.company_b)

    def test_03_prevent_active_toggle_with_moves(self):
        """Test that the constraint runs on active toggle as well (via manifest)."""
        self.env["account.move"].create(
            {
                "move_type": "entry",
                "partner_id": self.partner.id,
                "company_id": self.company_a.id,
                "line_ids": [
                    Command.create({"name": "line1", "account_id": self.account.id}),
                    Command.create({"name": "line2", "account_id": self.account.id}),
                ],
            }
        )
        with self.assertRaises(ValidationError):
            self.partner.sudo().write({"company_id": self.company_b.id})
