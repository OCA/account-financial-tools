# Copyright 2015 Pedro M. Baeza
# Copyright 2017 Tecnativa - Vicent Cubells
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

import odoo.tests.common as common
from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged


@tagged("post_install")
class TestAccountNetting(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        res_users_account_manager = cls.env.ref("account.group_account_manager")
        partner_manager = cls.env.ref("base.group_partner_manager")
        cls.env.user.write(
            {"groups_id": [(6, 0, [res_users_account_manager.id, partner_manager.id])]}
        )
        cls.company = cls.env.ref("base.main_company")
        # only adviser can create an account
        cls.aa_model = cls.env["account.account"]
        cls.account_receivable = cls._get_account(cls, "receivable")
        cls.account_payable = cls._get_account(cls, "payable")
        cls.account_revenue = cls._get_account(cls, "revenue")
        cls.account_expense = cls._get_account(cls, "expenses")
        cls.partner_model = cls.env["res.partner"]
        cls.partner = cls._create_partner(cls, "Supplier/Customer")
        cls.partner1 = cls._create_partner(cls, "Supplier/Customer 1")
        cls.miscellaneous_journal = cls.env["account.journal"].search(
            [("type", "=", "general")], limit=1
        )
        # We need a product with taxes at 0 so that the amounts are as expected.
        cls.account_tax = cls.env["account.tax"].create(
            {"name": "0%", "amount_type": "fixed", "type_tax_use": "sale", "amount": 0}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product Test",
                "list_price": 10,
                "taxes_id": [(6, 0, [cls.account_tax.id])],
            }
        )
        out_invoice_partner = cls._create_move(cls, "out_invoice", cls.partner, 100)
        out_invoice_partner.action_post()
        cls.move_line_1 = out_invoice_partner.line_ids.filtered(
            lambda x: x.account_id == cls.account_receivable
        )
        in_invoice_partner = cls._create_move(cls, "in_invoice", cls.partner, 1200)
        in_invoice_partner.action_post()
        cls.move_line_2 = in_invoice_partner.line_ids.filtered(
            lambda x: x.account_id == cls.account_payable
        )
        cls.move_line_3 = in_invoice_partner.line_ids.filtered(
            lambda x: x.account_id == cls.account_expense
        )
        in_invoice_partner1 = cls._create_move(cls, "in_invoice", cls.partner1, 200)
        in_invoice_partner1.action_post()
        cls.move_line_4 = in_invoice_partner1.line_ids.filtered(
            lambda x: x.account_id == cls.account_payable
        )
        in_refund_partner1 = cls._create_move(cls, "in_refund", cls.partner1, 200)
        in_refund_partner1.action_post()
        cls.move_line_5 = in_refund_partner1.line_ids.filtered(
            lambda x: x.account_id == cls.account_payable
        )
        in_refund_partner1 = cls._create_move(cls, "in_refund", cls.partner1, 200)
        in_refund_partner1.action_post()
        cls.move_line_6 = in_refund_partner1.line_ids.filtered(
            lambda x: x.account_id == cls.account_payable
        )

    def _get_account(self, user_type):
        user_type_ref = "account.data_account_type_%s" % user_type
        return self.aa_model.search(
            [
                ("user_type_id", "=", self.env.ref(user_type_ref).id),
                ("company_id", "=", self.company.id),
            ],
            limit=1,
        )

    def _create_partner(self, name):
        return self.partner_model.create(
            {
                "name": name,
                "property_account_receivable_id": self.account_receivable.id,
                "property_account_payable_id": self.account_payable.id,
            }
        )

    def _create_move(self, move_type, partner, price):
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type=move_type,
            )
        )
        move_form.partner_id = partner
        move_form.invoice_date = datetime.now()
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.price_unit = price
        return move_form.save()

    def test_compensation(self):
        # Test exception line 33 from account_move_make_netting
        obj = self.env["account.move.make.netting"].with_context(
            active_ids=[self.move_line_1.id]
        )
        with self.assertRaises(ValidationError):
            wizard = obj.create(
                {
                    "move_line_ids": [(6, 0, [self.move_line_1.id])],
                    "journal_id": self.miscellaneous_journal.id,
                }
            )
        # Test exception line 39 from account_move_make_netting
        obj = self.env["account.move.make.netting"].with_context(
            active_ids=[self.move_line_1.id, self.move_line_3.id]
        )
        with self.assertRaises(ValidationError):
            wizard = obj.create(
                {
                    "move_line_ids": [
                        (6, 0, [self.move_line_1.id, self.move_line_3.id])
                    ],
                    "journal_id": self.miscellaneous_journal.id,
                }
            )
        # Test exception line 45 from account_move_make_netting
        obj = self.env["account.move.make.netting"].with_context(
            active_ids=[self.move_line_4.id, self.move_line_5.id]
        )
        with self.assertRaises(ValidationError):
            wizard = obj.create(
                {
                    "move_line_ids": [
                        (6, 0, [self.move_line_4.id, self.move_line_5.id])
                    ],
                    "journal_id": self.miscellaneous_journal.id,
                }
            )
        # Test exception line 42 from account_move_make_netting
        moves = self.env["account.move.line"].browse(
            [self.move_line_4.id, self.move_line_5.id]
        )
        moves.reconcile()
        obj = self.env["account.move.make.netting"].with_context(
            active_ids=[self.move_line_4.id, self.move_line_5.id]
        )
        with self.assertRaises(ValidationError):
            wizard = obj.create(
                {
                    "move_line_ids": [
                        (6, 0, [self.move_line_4.id, self.move_line_5.id])
                    ],
                    "journal_id": self.miscellaneous_journal.id,
                }
            )
        # Test exception line 52 from account_move_make_netting
        obj = self.env["account.move.make.netting"].with_context(
            active_ids=[self.move_line_1.id, self.move_line_6.id]
        )
        with self.assertRaises(ValidationError):
            wizard = obj.create(
                {
                    "move_line_ids": [
                        (6, 0, [self.move_line_1.id, self.move_line_6.id])
                    ],
                    "journal_id": self.miscellaneous_journal.id,
                }
            )
        obj = self.env["account.move.make.netting"].with_context(
            active_ids=[self.move_line_1.id, self.move_line_2.id]
        )
        wizard = obj.create(
            {
                "move_line_ids": [(6, 0, [self.move_line_1.id, self.move_line_2.id])],
                "journal_id": self.miscellaneous_journal.id,
            }
        )
        res = wizard.button_compensate()
        move = self.env["account.move"].browse(res["res_id"])
        self.assertEqual(
            len(move.line_ids), 2, "AR/AP netting move has an incorrect line number"
        )
        move_line_receivable = move.line_ids.filtered(
            lambda x: x.account_id == self.account_receivable
        )
        self.assertEqual(
            move_line_receivable.credit,
            100,
            "Incorrect credit amount for receivable move line",
        )
        self.assertTrue(
            move_line_receivable.reconciled and move_line_receivable.full_reconcile_id,
            "Receivable move line should be totally reconciled",
        )
        move_line_payable = move.line_ids.filtered(
            lambda x: x.account_id == self.account_payable
        )
        self.assertEqual(
            move_line_payable.debit, 100, "Incorrect debit amount for payable move line"
        )
        self.assertTrue(
            move_line_payable.reconciled and not move_line_payable.full_reconcile_id,
            "Receivable move line should be partially reconciled",
        )
