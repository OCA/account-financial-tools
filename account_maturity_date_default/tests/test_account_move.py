from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMove(AccountTestInvoicingCommon):
    def test_invoice_move_update(self):
        invoice = self.init_invoice("out_invoice", products=[self.product])
        invoice.line_ids.write({"date_maturity": False})
        invoice.write({"date": "1999-12-31"})
        invoice_line = invoice.line_ids.filtered(
            lambda x: x.account_id.account_type == "asset_receivable"
        )
        self.assertEqual(
            invoice_line.date_maturity, fields.Date.from_string("1999-12-31")
        )
