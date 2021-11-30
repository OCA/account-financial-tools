# Copyright 2021 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests import common


class TestAccountMoveLineCurrency(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        res_users_account_manager = cls.env.ref("account.group_account_manager")
        partner_manager = cls.env.ref("base.group_partner_manager")
        cls.env.user.write(
            {"groups_id": [(6, 0, [res_users_account_manager.id, partner_manager.id])]}
        )

        # Partner
        cls.res_partner_1 = cls.env["res.partner"].create({"name": "Wood Corner"})

        # Products
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Desk Combination", "list_price": 100}
        )
        cls.product_2 = cls.env["product.product"].create(
            {"name": "Desk Combination 2", "list_price": 100}
        )

        # Tax
        cls.tax = cls.env["account.tax"].create(
            {"name": "Tax 15", "type_tax_use": "sale", "amount": 20}
        )

        # Currencies
        cls.currency_euro = cls.env["res.currency"].search([("name", "=", "EUR")])
        cls.currency_usd = cls.env["res.currency"].search([("name", "=", "USD")])
        cls.currency_rate = cls.env["res.currency.rate"].create(
            {"rate": 1.30, "currency_id": cls.currency_usd.id}
        )

        # Invoices
        cls.invoice_1 = cls.env["account.move"].create(
            [
                {
                    "type": "out_invoice",
                    "partner_id": cls.res_partner_1.id,
                    "currency_id": cls.currency_euro.id,
                    "invoice_line_ids": [
                        (
                            0,
                            None,
                            {
                                "product_id": cls.product_1.id,
                                "product_uom_id": cls.product_1.uom_id.id,
                                "quantity": 12,
                                "price_unit": 1000,
                                "tax_ids": cls.tax,
                            },
                        ),
                    ],
                }
            ]
        )
        cls.invoice_2 = cls.env["account.move"].create(
            [
                {
                    "type": "out_invoice",
                    "partner_id": cls.res_partner_1.id,
                    "currency_id": cls.currency_usd.id,
                    "invoice_line_ids": [
                        (
                            0,
                            None,
                            {
                                "product_id": cls.product_2.id,
                                "product_uom_id": cls.product_2.uom_id.id,
                                "quantity": 10,
                                "price_unit": 500,
                                "tax_ids": cls.tax,
                            },
                        ),
                    ],
                }
            ]
        )

        cls.invoice_1.action_post()
        cls.invoice_2.action_post()

    def test_account_move_line_used_currency(self):
        self.assertEqual(
            self.invoice_1.amount_total, 14400,
        )

        self.assertEqual(
            self.invoice_2.amount_total, 6000,
        )

        item_1 = self.env["account.move.line"].browse(
            self.invoice_1.invoice_line_ids.id
        )
        self.assertEqual(
            item_1.amount_used_currency, -12000,
        )

        self.assertEqual(
            item_1.used_currency_id.id, self.currency_euro.id,
        )

        item_2 = self.env["account.move.line"].browse(
            self.invoice_2.invoice_line_ids.id
        )
        self.assertEqual(
            item_2.amount_used_currency, -5000,
        )

        self.assertEqual(
            item_2.used_currency_id.id, self.currency_usd.id,
        )
