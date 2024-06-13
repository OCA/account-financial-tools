# Copyright 2024 Foodles (https://www.foodles.co/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common


class TestAccountInvoiceConstraintChronologyWithDateRange(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.ref("base.main_company")
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        cls.today = fields.Date.today()

        cls.sale_sequence = cls.env["ir.sequence"].create(
            {
                "name": "Sale sequence",
                "implementation": "no_gap",
                "code": "sale.sequence",
                "padding": 4,
                "use_date_range": True,
                "prefix": "INV/%(year)s/%(month)s/",
                "number_increment": 1,
                "date_range_ids": [
                    (
                        0,
                        0,
                        {
                            "date_from": cls.today - timedelta(days=1),
                            "date_to": cls.today + timedelta(days=1),
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "date_from": cls.today + timedelta(days=2),
                            "date_to": cls.today + timedelta(days=4),
                        },
                    ),
                ],
            }
        )

        cls.AccountJournal = cls.env["account.journal"]
        cls.sale_journal = cls.AccountJournal.create(
            {
                "name": "Sale journal",
                "code": "SALE",
                "type": "sale",
                "check_chronology": True,
                "sequence_id": cls.sale_sequence.id,
            }
        )

        cls.ProductProduct = cls.env["product.product"]
        cls.product = cls.ProductProduct.create({"name": "Product"})

        cls.AccountMove = cls.env["account.move"]
        with common.Form(
            cls.AccountMove.with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.invoice_date = cls.today
            invoice_form.partner_id = cls.partner_2
            invoice_form.journal_id = cls.sale_journal
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = cls.product
            cls.invoice_1 = invoice_form.save()
        cls.invoice_2 = cls.invoice_1.copy()

    def test_validate_invoices_with_different_ranges_but_older_first(self):
        self.invoice_2.invoice_date = self.today
        self.invoice_1.invoice_date = self.today + timedelta(days=3)
        self.invoice_2.action_post()
        self.invoice_1.action_post()

    def test_validate_invoices_with_different_ranges_but_newer_first(self):
        self.invoice_2.invoice_date = self.today + timedelta(days=3)
        self.invoice_1.invoice_date = self.today
        self.invoice_1.action_post()
        self.invoice_2.action_post()

    def test_validate_invoice_with_same_range_raise_error_from_older_draft_invoice(
        self,
    ):
        self.invoice_2.invoice_date = self.today + timedelta(days=1)
        self.invoice_1.invoice_date = self.today
        with self.assertRaises(UserError):
            self.invoice_2.action_post()

    def test_validate_invoices_with_same_range_raise_error_from_newer_validated_invoice(
        self,
    ):
        self.invoice_1.invoice_date = False
        self.invoice_2.invoice_date = self.today + timedelta(days=1)
        self.invoice_2.action_post()
        self.invoice_1.invoice_date = self.today
        with self.assertRaises(UserError):
            self.invoice_1.action_post()

    @patch(
        "odoo.addons.account_invoice_constraint_chronology.model."
        "account_move.AccountMove._get_older_conflicting_invoices_domain"
    )
    @patch(
        "odoo.addons.account_invoice_constraint_chronology.model."
        "account_move.AccountMove._get_newer_conflicting_invoices_domain"
    )
    def test_validate_invoice_without_date_range_call_super(
        self,
        mock_get_newer_conflicting_invoices_domain,
        mock_get_older_conflicting_invoices_domain,
    ):
        mock_get_older_conflicting_invoices_domain.return_value = [
            ("journal_id", "=", self.sale_journal.id),
            ("move_type", "!=", "entry"),
            ("state", "=", "draft"),
            ("invoice_date", "!=", False),
            ("invoice_date", "<", self.today),
        ]
        mock_get_newer_conflicting_invoices_domain.return_value = [
            ("journal_id", "=", self.sale_journal.id),
            ("move_type", "!=", "entry"),
            ("state", "=", "draft"),
            ("invoice_date", "!=", False),
            ("invoice_date", ">", self.today),
        ]

        self.sale_sequence.use_date_range = False

        self.invoice_1.invoice_date = self.today
        self.invoice_1.action_post()
        mock_get_older_conflicting_invoices_domain.assert_called_once()
        mock_get_newer_conflicting_invoices_domain.assert_called_once()
