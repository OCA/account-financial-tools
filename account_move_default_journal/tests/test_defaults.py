# Copyright 2023 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import TransactionCase


class TestDefaults(TransactionCase):
    def setUp(self):
        super().setUp()
        self.different_currency = self.env["res.currency"].create(
            {
                "name": "Test Currency",
                "symbol": "?",
            }
        )
        self.company = self.env.ref("base.main_company")
        # This journal gets selected before the 'General Journal' because of its code:
        self.journal_first = self.env["account.journal"].create(
            {
                "name": "First Journal",
                "code": "1st",
                "type": "general",
                "company_id": self.company.id,
            }
        )
        self.journal_general = self.env["account.journal"].create(
            {
                "name": "General Journal",
                "code": "GJ",
                "type": "general",
                "company_id": self.company.id,
                "currency_id": self.different_currency.id,
            }
        )
        self.journal_sale = self.env["account.journal"].create(
            {
                "name": "Sale Journal",
                "code": "SJ",
                "type": "sale",
                "company_id": self.company.id,
            }
        )
        self.journal_purchase = self.env["account.journal"].create(
            {
                "name": "Purchase Journal",
                "code": "PJ",
                "type": "purchase",
                "company_id": self.company.id,
            }
        )

    def test_defaults(self):
        # Test whether the first journal gets selected with no default set
        move = self.env["account.move"].create({"move_type": "entry"})
        self.assertNotEqual(move.journal_id, self.journal_general)

        # Test whether the journal with the relevant currency is chosen
        move = (
            self.env["account.move"]
            .with_context({"default_currency_id": self.different_currency.id})
            .create({"move_type": "entry"})
        )
        self.assertEqual(move.journal_id, self.journal_general)
        move = (
            self.env["account.move"]
            .with_context({"default_currency_id": self.different_currency.id})
            .create({"move_type": "out_invoice"})
        )
        self.assertNotEqual(move.journal_id, self.journal_general)

        # Test whether the correct default journals are chosen
        self.company.default_general_journal_id = self.journal_general
        self.company.default_sale_journal_id = self.journal_sale
        self.company.default_purchase_journal_id = self.journal_purchase
        move = self.env["account.move"].create({"move_type": "entry"})
        self.assertEqual(move.journal_id, self.journal_general)
        move = self.env["account.move"].create({"move_type": "out_invoice"})
        self.assertEqual(move.journal_id, self.journal_sale)
        move = self.env["account.move"].create({"move_type": "in_invoice"})
        self.assertEqual(move.journal_id, self.journal_purchase)
