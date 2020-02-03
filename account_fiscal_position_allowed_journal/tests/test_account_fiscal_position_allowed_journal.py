# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase


class TestAccountFiscalPositionAllowedJournal(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountFiscalPositionAllowedJournal, cls).setUpClass()

        # MODELS
        cls.account_model = cls.env["account.account"]
        cls.fiscal_position_model = cls.env["account.fiscal.position"]
        cls.invoice_model = cls.env["account.move"]
        cls.journal_model = cls.env["account.journal"]
        cls.partner_model = cls.env["res.partner"]

        # INSTANCES
        cls.account_account_01 = cls.account_model.search(
            [("code", "ilike", "4%")], limit=1
        )
        cls.fiscal_position_01 = cls.fiscal_position_model.create(
            {"name": "Fiscal position 01"}
        )
        cls.journal_01 = cls.journal_model.search([("type", "=", "sale")], limit=1)
        cls.journal_02 = cls.journal_01.copy()
        cls.partner_01 = cls.partner_model.search([], limit=1)
        cls.invoice_01 = cls.invoice_model.create(
            {
                "type": "out_invoice",
                "partner_id": cls.partner_01.id,
                "journal_id": cls.journal_01.id,
                "fiscal_position_id": cls.fiscal_position_01.id,
                "invoice_line_ids": [
                    (
                        0,
                        None,
                        {
                            "name": "Invoice line 01",
                            "price_unit": 1,
                            "quantity": 1,
                            "account_id": cls.account_account_01.id,
                        },
                    )
                ],
            }
        )

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
        self.invoice_01.post()
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
            self.invoice_01.post()
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
        self.invoice_01.post()
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
