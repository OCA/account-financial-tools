# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import Form

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
        cls.account_account_01 = cls.env["account.account"].create(
            {
                "user_type_id": cls.env.ref("account.data_account_type_expenses").id,
                "code": "EXPTEST",
                "name": "Test expense account",
            }
        )

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
        cls.partner_01 = cls.partner_model.search([], limit=1)

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
            line_form.product_id = cls.env.ref("product.product_product_4")
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
            - A draft invoice with a journal and no fiscal position
            - The fiscal position has an allowed journal, which is not the one
              selected on the invoice
        Test case:
            - Set the fiscal position on the invoice, trigger the onchange
        Expected result:
            - The journal is replaced by the on on the fiscal position
        """
        self.fiscal_position_01.allowed_journal_ids = [(6, 0, self.journal_02.ids)]
        self.assertEqual(self.invoice_01.state, "draft")
        self.assertNotIn(
            self.invoice_01.journal_id, self.fiscal_position_01.allowed_journal_ids
        )
        self.invoice_01._onchange_fiscal_position_allowed_journal()
        self.assertEqual(
            self.invoice_01.journal_id, self.fiscal_position_01.allowed_journal_ids[0]
        )
