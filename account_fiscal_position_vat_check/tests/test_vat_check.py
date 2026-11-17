# Copyright 2026 Moduon Team S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestVatCheck(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fiscal_position = cls.env["account.fiscal.position"].create(
            {"name": "VAT required", "vat_required": True}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Customer",
                "property_account_position_id": cls.fiscal_position.id,
            }
        )

    def _new_invoice(self, move_type="out_invoice"):
        return self._create_invoice(
            move_type=move_type,
            partner_id=self.partner,
            fiscal_position_id=self.fiscal_position.id,
            invoice_date="2019-01-01",
            invoice_line_ids=[self._prepare_invoice_line(product_id=self.product_a)],
        )

    def test_post_without_vat(self):
        for vat in (False, "", "/", "na", "NA"):
            self.partner.vat = vat
            invoice = self._new_invoice()
            with self.assertRaises(UserError, msg=f"VAT {vat!r} must be rejected"):
                invoice.action_post()

    def test_post_refund_without_vat(self):
        self.partner.vat = "/"
        refund = self._new_invoice("out_refund")
        with self.assertRaises(UserError):
            refund.action_post()

    def test_post_with_vat(self):
        self.partner.vat = "ESB12345674"
        invoice = self._new_invoice()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_post_vendor_bill_without_vat(self):
        self.partner.vat = "/"
        bill = self._new_invoice("in_invoice")
        bill.action_post()
        self.assertEqual(bill.state, "posted")

    def test_post_fiscal_position_without_vat_required(self):
        self.fiscal_position.vat_required = False
        self.partner.vat = "/"
        invoice = self._new_invoice()
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")

    def test_show_warning_vat_required(self):
        for vat, expected in (
            (False, True),
            ("", True),
            ("/", True),
            ("na", True),
            ("NA", True),
            ("ESB12345674", False),
        ):
            self.partner.vat = vat
            self.assertEqual(
                self.partner.show_warning_vat_required,
                expected,
                f"Unexpected warning flag for VAT {vat!r}",
            )
        self.partner.vat = "/"
        self.fiscal_position.vat_required = False
        self.assertFalse(self.partner.show_warning_vat_required)
