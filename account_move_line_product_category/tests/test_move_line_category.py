# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestAccountMoveLineCategory(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.move_obj = cls.env["account.move"]
        cls.move_line_obj = cls.env["account.move.line"]
        cls.company_id = cls.env.ref("base.main_company").id
        cls.category = cls.env["product.category"].create(
            {
                "name": "Category Move Line",
                "parent_id": cls.env.ref("product.product_category_all").id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Move Line",
                "categ_id": cls.category.id,
            }
        )
        cls.category_2 = cls.env["product.category"].create(
            {
                "name": "Category Move Line 2",
                "parent_id": cls.env.ref("product.product_category_all").id,
            }
        )
        cls.product_2 = cls.env["product.product"].create(
            {
                "name": "Product Move Line 2",
                "categ_id": cls.category_2.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test journal",
                "code": "COD",
                "type": "sale",
                "company_id": cls.company_id,
            }
        )

        cls.account_sale = cls.env["account.account"].create(
            {"name": "Test sale", "code": "700", "account_type": "income"}
        )
        cls.account_customer = cls.env["account.account"].create(
            {
                "name": "Test customer",
                "code": "430",
                "account_type": "expense",
                "reconcile": True,
            }
        )

    def _create_move(self, with_partner=True, amount=100):
        move_vals = {
            "journal_id": self.journal.id,
            "company_id": self.company_id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "/",
                        "debit": amount,
                        "credit": 0,
                        "account_id": self.account_customer.id,
                        "company_id": self.company_id,
                        "partner_id": with_partner and self.partner.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": "/",
                        "debit": 0,
                        "credit": amount,
                        "company_id": self.company_id,
                        "account_id": self.account_sale.id,
                        "product_id": self.product.id,
                    },
                ),
            ],
        }
        return self.move_obj.create(move_vals)

    def test_move(self):
        # Check if create and modifications to an account move line product
        # fill in the category coming from that product
        move = self._create_move()
        line = move.line_ids.filtered("product_id")
        self.assertEqual(self.category, line.categ_id)
        line.product_id = self.product_2
        self.assertEqual(self.category_2, line.categ_id)
