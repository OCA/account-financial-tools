# Copyright 2015 Pedro M. Baeza
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import odoo.tests.common as common


class TestAccountNetting(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountNetting, cls).setUpClass()
        res_users_account_manager = cls.env.ref("account.group_account_manager")
        partner_manager = cls.env.ref("base.group_partner_manager")
        cls.env.user.write(
            {"groups_id": [(6, 0, [res_users_account_manager.id, partner_manager.id])]}
        )
        # only adviser can create an account
        cls.account_receivable = cls.env["account.account"].create(
            {
                "code": "cust_acc",
                "name": "customer account",
                "user_type_id": cls.env.ref("account.data_account_type_receivable").id,
                "reconcile": True,
            }
        )
        cls.account_payable = cls.env["account.account"].create(
            {
                "code": "supp_acc",
                "name": "supplier account",
                "user_type_id": cls.env.ref("account.data_account_type_payable").id,
                "reconcile": True,
            }
        )
        cls.account_revenue = cls.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_revenue").id,
                )
            ],
            limit=1,
        )
        cls.account_expense = cls.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_expenses").id,
                )
            ],
            limit=1,
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Supplier/Customer",
                "property_account_receivable_id": cls.account_receivable.id,
                "property_account_payable_id": cls.account_payable.id,
            }
        )
        cls.partner1 = cls.env["res.partner"].create(
            {
                "name": "Supplier/Customer 1",
                "property_account_receivable_id": cls.account_receivable.id,
                "property_account_payable_id": cls.account_payable.id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {"name": "Test sale journal", "type": "sale", "code": "TEST"}
        )
        cls.expenses_journal = cls.env["account.journal"].create(
            {"name": "Test expense journal", "type": "purchase", "code": "EXP"}
        )
        cls.miscellaneous_journal = cls.env["account.journal"].create(
            {"name": "Miscellaneus journal", "type": "general", "code": "OTHER"}
        )
        cls.customer_invoice = cls.env["account.move"].create(
            {
                "journal_id": cls.journal.id,
                "type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test",
                            "price_unit": 100.0,
                            "account_id": cls.account_revenue.id,
                        },
                    )
                ],
            }
        )
        cls.customer_invoice.action_post()
        customer_move = cls.customer_invoice
        cls.move_line_1 = customer_move.line_ids.filtered(
            lambda x: x.account_id == cls.account_receivable
        )
        cls.supplier_invoice = cls.env["account.move"].create(
            {
                "journal_id": cls.expenses_journal.id,
                "type": "in_invoice",
                "partner_id": cls.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test",
                            "price_unit": 1200.0,
                            "account_id": cls.account_expense.id,
                        },
                    )
                ],
            }
        )
        cls.supplier_invoice.action_post()
        supplier_move = cls.supplier_invoice
        cls.move_line_2 = supplier_move.line_ids.filtered(
            lambda x: x.account_id == cls.account_payable
        )
        cls.move_line_3 = supplier_move.line_ids.filtered(
            lambda x: x.account_id == cls.account_expense
        )
        cls.supplier_invoice = cls.env["account.move"].create(
            {
                "journal_id": cls.expenses_journal.id,
                "type": "in_invoice",
                "partner_id": cls.partner1.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test",
                            "price_unit": 200.0,
                            "account_id": cls.account_expense.id,
                        },
                    )
                ],
            }
        )
        cls.supplier_invoice.action_post()
        supplier_move = cls.supplier_invoice
        cls.move_line_4 = supplier_move.line_ids.filtered(
            lambda x: x.account_id == cls.account_payable
        )
        cls.supplier_invoice = cls.env["account.move"].create(
            {
                "journal_id": cls.expenses_journal.id,
                "type": "in_refund",
                "partner_id": cls.partner1.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test",
                            "price_unit": 200.0,
                            "account_id": cls.account_expense.id,
                        },
                    )
                ],
            }
        )
        cls.supplier_invoice.action_post()
        supplier_move = cls.supplier_invoice
        cls.move_line_5 = supplier_move.line_ids.filtered(
            lambda x: x.account_id == cls.account_payable
        )
        cls.supplier_invoice = cls.env["account.move"].create(
            {
                "journal_id": cls.expenses_journal.id,
                "type": "in_refund",
                "partner_id": cls.partner1.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test",
                            "price_unit": 200.0,
                            "account_id": cls.account_expense.id,
                        },
                    )
                ],
            }
        )
        cls.supplier_invoice.action_post()
        supplier_move = cls.supplier_invoice
        cls.move_line_6 = supplier_move.line_ids.filtered(
            lambda x: x.account_id == cls.account_payable
        )

    def test_compensation(self):
        # Test exception line 33 from account_move_make_netting
        obj = self.env["account.move.make.netting"].with_context(
            active_ids=[self.move_line_1.id]
        )
        with self.assertRaises(Exception):
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
        with self.assertRaises(Exception):
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
        with self.assertRaises(Exception):
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
        with self.assertRaises(Exception):
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
        with self.assertRaises(Exception):
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
