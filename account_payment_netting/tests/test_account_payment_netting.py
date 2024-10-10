# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase


class TestAccountNetting(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.move_model = cls.env["account.move"]
        cls.payment_model = cls.env["account.payment"]
        cls.journal_model = cls.env["account.journal"]
        cls.register_payment_model = cls.env["account.payment.register"]

        cls.partner1 = cls.env.ref("base.res_partner_1")
        cls.partner2 = cls.env.ref("base.res_partner_2")

        cls.bank_journal = cls.journal_model.create(
            {
                "name": "Test bank journal",
                "type": "bank",
                "code": "TEBNK",
            }
        )
        cls.account_expense = cls.env["account.account"].search(
            [
                ("account_type", "=", "expense"),
                ("company_id", "=", cls.env.company.id),
            ],
            limit=1,
        )

    def create_invoice(self, move_type, partner, amount):
        """Returns an open invoice"""
        move = self.move_model.create(
            {
                "move_type": move_type,
                "invoice_date": fields.Date.today(),
                "partner_id": partner.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Test",
                            "price_unit": amount,
                            "tax_ids": [],
                        },
                    )
                ],
            }
        )
        return move

    def do_test_register_payment(
        self, invoices, expected_type, expected_diff, fully_paid=False, netting=True
    ):
        """Test create customer/supplier invoices. Then, select all invoices
        and make neting payment. I expect:
        - Payment Type (inbound or outbound) = expected_type
        - Payment amont = expected_diff
        - Payment can link to all invoices
        - All 4 invoices are in paid status"""
        # Select all invoices, and register payment
        ctx = {
            "active_ids": invoices.ids,
            "active_model": "account.move",
            "netting": netting,
        }
        with Form(self.register_payment_model.with_context(**ctx)) as f:
            f.journal_id = self.bank_journal
            f.amount = expected_diff
            if fully_paid:
                f.payment_difference_handling = "reconcile"
                f.writeoff_account_id = self.account_expense
        payment_wizard = f.save()
        # Diff amount = expected_diff, payment_type = expected_type
        self.assertEqual(payment_wizard.amount, expected_diff)
        self.assertEqual(payment_wizard.payment_type, expected_type)
        # Create payments
        res = payment_wizard.action_create_payments()
        payment = self.payment_model.browse(res["res_id"])
        # Payment can link to all invoices
        original_ids = (
            payment.reconciled_bill_ids + payment.reconciled_invoice_ids
        ).ids
        self.assertEqual(set(original_ids), set(invoices.ids))
        invoices = self.move_model.browse(invoices.ids)
        return invoices

    def test_1_payment_netting_neutral(self):
        """Test AR = AP"""
        # Create 2 AR Invoice, total amount = 200.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 100.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 100.0)
        # Create 2 AP Invoice, total amount = 200.0
        ap_inv_p1_1 = self.create_invoice("in_invoice", self.partner1, 100.0)
        ap_inv_p1_2 = self.create_invoice("in_invoice", self.partner1, 100.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "inbound", 0.0)
        # Test that all 4 invoices are paid
        self.assertEqual(list(set(invoices.mapped("state"))), ["posted"])
        self.assertEqual(list(set(invoices.mapped("payment_state"))), ["paid"])

    def test_2_payment_netting_inbound(self):
        """
        Test AR > AP:
            - Case1 AR > AP fully paid
            - Case2 AR > AP fully paid payment difference
            - Case3 AR > AP partially paid
            - Case4 AR > AP not paid
        """
        # ================ Case1 AR > AP fully paid ================
        # Create 2 AR Invoice, total amount = 200.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 100.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 100.0)
        # Create 2 AP Invoice, total amount = 160.0
        ap_inv_p1_1 = self.create_invoice("in_invoice", self.partner1, 80.0)
        ap_inv_p1_2 = self.create_invoice("in_invoice", self.partner1, 80.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "inbound", 40.0)
        # Test that all 4 invoices are paid
        self.assertEqual(list(set(invoices.mapped("state"))), ["posted"])
        self.assertEqual(list(set(invoices.mapped("payment_state"))), ["paid"])

        # ================ Case2 AR > AP fully paid with payment difference ================
        # Create 2 AR Invoice, total amount = 200.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 100.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 100.0)
        # Create 2 AP Invoice, total amount = 160.0
        ap_inv_p1_1 = self.create_invoice("in_invoice", self.partner1, 80.0)
        ap_inv_p1_2 = self.create_invoice("in_invoice", self.partner1, 80.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "inbound", 30.0, True)
        # Test that all 4 invoices are paid
        self.assertEqual(list(set(invoices.mapped("state"))), ["posted"])
        self.assertEqual(list(set(invoices.mapped("payment_state"))), ["paid"])

        # ================ Case3 AR > AP partial ================
        # Create 2 AR Invoice, total amount = 200.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 100.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 100.0)
        # Create 2 AP Invoice, total amount = 160.0
        ap_inv_p1_1 = self.create_invoice("in_invoice", self.partner1, 80.0)
        ap_inv_p1_2 = self.create_invoice("in_invoice", self.partner1, 80.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "inbound", 30.0)
        # Test that all 4 invoices are paid and partial
        self.assertEqual(list(set(invoices.mapped("state"))), ["posted"])
        self.assertIn("paid", list(set(invoices.mapped("payment_state"))))
        self.assertIn("partial", list(set(invoices.mapped("payment_state"))))

        # ================ Case4 AR > AP not paid ================
        # Create 2 AR Invoice, total amount = 200.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 100.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 100.0)
        # Create 2 AP Invoice, total amount = 160.0
        ap_inv_p1_1 = self.create_invoice("in_invoice", self.partner1, 80.0)
        ap_inv_p1_2 = self.create_invoice("in_invoice", self.partner1, 80.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "inbound", 0.0)
        # Test that all 4 invoices are paid and partial
        self.assertEqual(list(set(invoices.mapped("state"))), ["posted"])
        self.assertIn("paid", list(set(invoices.mapped("payment_state"))))
        self.assertIn("partial", list(set(invoices.mapped("payment_state"))))

    def test_3_payment_netting_outbound(self):
        """
        Test AR < AP:
            - Case1 AR < AP fully paid
            - Case2 AR < AP fully paid payment difference
            - Case3 AR < AP partially paid
            - Case4 AR < AP not paid
        """
        # ================ Case1 AR < AP fully paid ================
        # Create 2 AR Invoice, total amount = 160.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 80.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 80.0)
        # Create 2 AP Invoice, total amount = 200.0
        ap_inv_p1_1 = self.create_invoice("in_invoice", self.partner1, 100.0)
        ap_inv_p1_2 = self.create_invoice("in_invoice", self.partner1, 100.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "outbound", 40.0)
        # Test that all 4 invoices are paid
        self.assertEqual(list(set(invoices.mapped("state"))), ["posted"])
        self.assertEqual(list(set(invoices.mapped("payment_state"))), ["paid"])

        # ================ Case2 AR < AP fully paid with payment difference ================
        # Create 2 AR Invoice, total amount = 160.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 80.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 80.0)
        # Create 2 AP Invoice, total amount = 200.0
        ap_inv_p1_1 = self.create_invoice("in_invoice", self.partner1, 100.0)
        ap_inv_p1_2 = self.create_invoice("in_invoice", self.partner1, 100.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "outbound", 30.0, True)

        # ================ Case3 AR < AP partially paid ================
        # Create 2 AR Invoice, total amount = 160.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 80.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 80.0)
        # Create 2 AP Invoice, total amount = 200.0
        ap_inv_p1_1 = self.create_invoice("in_invoice", self.partner1, 100.0)
        ap_inv_p1_2 = self.create_invoice("in_invoice", self.partner1, 100.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "outbound", 30.0)
        # Test that all 4 invoices are paid and partial
        self.assertEqual(list(set(invoices.mapped("state"))), ["posted"])
        self.assertIn("paid", list(set(invoices.mapped("payment_state"))))
        self.assertIn("partial", list(set(invoices.mapped("payment_state"))))

        # ================ Case4 AR < AP not paid ================
        # Create 2 AR Invoice, total amount = 160.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 80.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 80.0)
        # Create 2 AP Invoice, total amount = 200.0
        ap_inv_p1_1 = self.create_invoice("in_invoice", self.partner1, 100.0)
        ap_inv_p1_2 = self.create_invoice("in_invoice", self.partner1, 100.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "outbound", 0.0)
        # Test that all 4 invoices are paid and partial
        self.assertEqual(list(set(invoices.mapped("state"))), ["posted"])
        self.assertIn("paid", list(set(invoices.mapped("payment_state"))))
        self.assertIn("partial", list(set(invoices.mapped("payment_state"))))

    def test_4_payment_netting_for_one_invoice(self):
        """Test only 1 customer invoice, should also pass test"""
        invoices = self.create_invoice("out_invoice", self.partner1, 80.0)
        invoices.action_post()
        self.do_test_register_payment(invoices, "inbound", 80.0)

    def test_5_payment_netting_for_multi_bill(self):
        """Test multi bills, should also pass test"""
        # Create 2 AP Invoice, total amount = 200.0
        ap_inv_p1_1 = self.create_invoice("in_invoice", self.partner1, 100.0)
        ap_inv_p1_2 = self.create_invoice("in_invoice", self.partner1, 100.0)
        # Test Register Payment
        invoices = ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "outbound", 200.0)
        # Test that all 2 bills are paid
        self.assertEqual(list(set(invoices.mapped("state"))), ["posted"])
        self.assertEqual(list(set(invoices.mapped("payment_state"))), ["paid"])

    def test_6_payment_netting_for_multi_invoices(self):
        """Test multi invoices, should also pass test"""
        # Create 2 AR Invoice, total amount = 200.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 100.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 100.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2
        invoices.action_post()
        self.do_test_register_payment(invoices, "inbound", 200.0)
        # Test that all 2 invoices are paid
        self.assertEqual(list(set(invoices.mapped("state"))), ["posted"])
        self.assertEqual(list(set(invoices.mapped("payment_state"))), ["paid"])

    def test_7_payment_netting_wrong_partner_exception(self):
        """Test when not invoices on same partner, show warning"""
        # Create 2 AR Invoice, total amount = 160.0
        ar_inv_p1_1 = self.create_invoice("out_invoice", self.partner1, 80.0)
        ar_inv_p1_2 = self.create_invoice("out_invoice", self.partner1, 80.0)
        # Create 1 AP Invoice, amount = 200.0, using different partner 2
        ap_inv_p2 = self.create_invoice("in_invoice", self.partner2, 200.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p2
        invoices.action_post()
        with self.assertRaises(UserError) as e:
            self.do_test_register_payment(invoices, "outbound", 40.0)
        self.assertEqual(
            e.exception.args[0], "All invoices must belong to same partner"
        )

    def test_8_payment_normal_process(self):
        """Test only 1 customer invoice, should also pass test"""
        invoices = self.create_invoice("out_invoice", self.partner1, 80.0)
        invoices.action_post()
        self.do_test_register_payment(invoices, "inbound", 80.0, netting=False)
