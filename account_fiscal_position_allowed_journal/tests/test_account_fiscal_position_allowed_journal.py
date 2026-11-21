# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountFiscalPositionAllowedJournal(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # MODELS
        cls.account_model = cls.env["account.account"]
        cls.fiscal_position_model = cls.env["account.fiscal.position"]
        cls.invoice_model = cls.env["account.move"]
        cls.journal_model = cls.env["account.journal"]
        cls.partner_model = cls.env["res.partner"]

        # INSTANCES

        cls.fiscal_position_01 = cls.fiscal_position_model.create(
            {"name": "Fiscal position 01"}
        )
        cls.journal_01 = cls.journal_model.create(
            {
                "name": "Test journal",
                "code": "TEST",
                "type": "sale",
            }
        )
        cls.journal_02 = cls.journal_01.copy()
        cls.partner_01 = cls.partner_model.create({"name": "Test partner 01"})
        cls.product_01 = cls.env["product.product"].create({"name": "Test product 01"})

        move_form = Form(
            cls.env["account.move"].with_context(
                default_move_type="out_invoice", check_move_validity=False
            )
        )
        move_form.invoice_date = fields.Date.context_today(cls.env.user)
        move_form.partner_id = cls.partner_01
        move_form.journal_id = cls.journal_01
        move_form.fiscal_position_id = cls.fiscal_position_01
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "Invoice line 01"
            line_form.product_id = cls.product_01
            line_form.price_unit = 1
            line_form.quantity = 1
        cls.invoice_01 = move_form.save()

    def test_01(self):
        """
        Data:
            - A draft invoice with a journal and a fiscal position
            - The fiscal position has no allowed journal
        Test case:
            - Validate the invoice
        Expected result:
            - The invoice is validated
        """
        self.assertEqual(self.invoice_01.state, "draft")
        self.invoice_01.action_post()
        self.assertEqual(self.invoice_01.state, "posted")

    def test_02(self):
        """
        Data:
            - A draft invoice with a journal and a fiscal position
            - The fiscal position has an allowed journal, which is not
              the one selected on the invoice
        Test case:
            - Validate the invoice
        Expected result:
            - UseError is raised
        """
        self.fiscal_position_01.allowed_journal_ids = [(6, 0, self.journal_02.ids)]
        self.assertEqual(self.invoice_01.state, "draft")
        with self.assertRaises(UserError):
            self.invoice_01.action_post()
        self.assertEqual(self.invoice_01.state, "draft")

    def test_03(self):
        """
        Data:
            - A draft invoice with a journal and a fiscal position
            - The fiscal position has an allowed journal, which is the one
              selected on the invoice
        Test case:
            - Validate the invoice
        Expected result:
            - This invoice is validated
        """
        self.fiscal_position_01.allowed_journal_ids = [(6, 0, self.journal_01.ids)]
        self.assertEqual(self.invoice_01.state, "draft")
        self.invoice_01.action_post()
        self.assertEqual(self.invoice_01.state, "posted")

    def test_04(self):
        """
        Data:
            - The fiscal position has a single allowed journal
        Test case:
            - Create a new invoice and set the fiscal position, which
              triggers the journal recomputation
        Expected result:
            - The journal is set to the one allowed by the fiscal position
        """
        self.fiscal_position_01.allowed_journal_ids = [(6, 0, self.journal_02.ids)]
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice", check_move_validity=False
            )
        )
        move_form.invoice_date = fields.Date.context_today(self.env.user)
        move_form.partner_id = self.partner_01
        move_form.fiscal_position_id = self.fiscal_position_01
        with move_form.invoice_line_ids.new() as line_form:
            line_form.name = "Invoice line 01"
            line_form.product_id = self.product_01
            line_form.price_unit = 1
            line_form.quantity = 1
        invoice = move_form.save()
        self.assertEqual(invoice.state, "draft")
        self.assertIn(invoice.journal_id, self.fiscal_position_01.allowed_journal_ids)
        self.assertEqual(
            invoice.journal_id, self.fiscal_position_01.allowed_journal_ids[0]
        )
