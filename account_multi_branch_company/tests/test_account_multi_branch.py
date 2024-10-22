# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMultiBranchCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.branch_model = cls.env["res.branch"]
        cls.move_model = cls.env["account.move"]
        cls.journal_model = cls.env["account.journal"]
        cls.register_payment_model = cls.env["account.payment.register"]
        cls.main_company = cls.env.ref("base.main_company")
        cls.partner1 = cls.env.ref("base.res_partner_1")
        cls.product1 = cls.env.ref("product.product_product_7")
        cls.branch1 = cls.branch_model.create(
            {
                "name": "00000",
                "company_id": cls.main_company.id,
                "email": "main_company@branch1.com",
            }
        )
        cls.branch2 = cls.branch_model.create(
            {
                "name": "00001",
                "company_id": cls.main_company.id,
                "email": "main_company@branch2.com",
            }
        )
        cls.journal = cls.journal_model.create(
            {"name": "Test journal", "code": "TEST", "type": "purchase"}
        )
        cls.payment_method_manual_in = cls.env.ref(
            "account.account_payment_method_manual_in"
        )

    def _create_move(self, move_type):
        move = self.move_model.create(
            {
                "partner_id": self.partner1.id,
                "invoice_date": fields.Date.today(),
                "move_type": move_type,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product1.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        return move

    def test_01_create_vendor_bill_branch(self):
        move = self._create_move("in_invoice")
        self.assertFalse(move.branch_id)
        move.branch_id = self.branch1.id
        self.assertEqual(move.branch_id, self.branch1)
        move.action_post()
        move2 = self._create_move("in_invoice")
        move2.branch_id = self.branch2.id
        self.assertEqual(move2.branch_id, self.branch2)
        move2.action_post()
        # Not allow register payment with difference branch
        with self.assertRaises(UserError):
            register_payments = self.register_payment_model.with_context(
                active_model="account.move",
                active_ids=[move.id, move2.id],
            ).create({"group_payment": True})
            payment = register_payments._create_payments()
        register_payments = self.register_payment_model.with_context(
            active_model="account.move",
            active_ids=[move.id],
        ).create({"group_payment": True})
        payment = register_payments._create_payments()
        self.assertAlmostEqual(payment.amount, 100)
        self.assertEqual(payment.branch_id, self.branch1)
        self.assertEqual(payment.move_id.branch_id, self.branch1)
