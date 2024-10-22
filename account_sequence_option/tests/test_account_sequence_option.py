# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from datetime import timedelta

from odoo import fields
from odoo.tests.common import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountSequenceOption(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountMove = cls.env["account.move"]
        cls.AccountMoveLine = cls.env["account.move.line"]
        cls.partner_id = cls.env.ref("base.res_partner_1")
        cls.product_id_1 = cls.env.ref("product.product_product_6")
        cls.account_seq_opt1 = cls.env.ref("account_sequence_option.account_sequence")
        cls.pay_in = cls.env.ref("account.account_payment_method_manual_in")
        cls.pay_out = cls.env.ref("account.account_payment_method_manual_out")

    @classmethod
    def _create_invoice(self, move_type):
        move_form = Form(
            self.env["account.move"].with_context(default_move_type=move_type)
        )
        move_form.partner_id = self.partner_id
        move_form.invoice_date = fields.Date.today()
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_id_1
        invoice = move_form.save()
        return invoice

    @classmethod
    def _create_payment(self, payment_type, partner_type):
        ctx = {
            "default_payment_type": payment_type,
            "default_partner_type": partner_type,
            "default_move_journal_types": ("bank", "cash"),
        }
        move_form = Form(self.env["account.payment"].with_context(**ctx))
        move_form.partner_id = self.partner_id
        payment = move_form.save()
        return payment

    def test_account_sequence_options(self):
        """Test different kind of sequences
        1. Customer Invoice 2. Vendor Bill
        3. Customer Refund 4. Vendor Refund
        5. Customer Payment 6. Vendor Payment
        """
        self.account_seq_opt1.use_sequence_option = True
        # 1. Customer Invoice
        self.invoice = self._create_invoice("out_invoice")
        self.invoice.action_post()
        self.invoice._compute_name()
        name = hasattr(self.env["account.journal"], "sequence_id") and "INV" or "CINV"
        self.assertIn(name, self.invoice.name)
        # 2. Vendor Bill
        self.invoice = self._create_invoice("in_invoice")
        self.invoice.action_post()
        name = hasattr(self.env["account.journal"], "sequence_id") and "BILL" or "VBIL"
        self.assertIn(name, self.invoice.name)
        # 3. Customer Refund
        self.invoice = self._create_invoice("out_refund")
        self.invoice.action_post()
        name = hasattr(self.env["account.journal"], "sequence_id") and "RINV" or "CREF"
        self.assertIn(name, self.invoice.name)
        # 4. Vendor Refund
        self.invoice = self._create_invoice("in_refund")
        self.invoice.action_post()
        name = hasattr(self.env["account.journal"], "sequence_id") and "RBILL" or "VREF"
        self.assertIn(name, self.invoice.name)
        # 5. Customer Payment
        self.payment = self._create_payment("inbound", "customer")
        self.payment.action_post()
        name = hasattr(self.env["account.journal"], "sequence_id") and "BNK1" or "CPAY"
        self.assertIn(name, self.payment.name)
        # 6. Vendor Payment
        self.payment = self._create_payment("outbound", "supplier")
        self.payment.action_post()
        name = hasattr(self.env["account.journal"], "sequence_id") and "BNK1" or "VPAY"
        self.assertIn(name, self.payment.name)
        # 7. Create out invoice, post invoice, reset invoice to Draft
        #       Change Date, post invoice.
        self.invoice = self._create_invoice("out_invoice")
        self.invoice.action_post()
        old_name = self.invoice.name
        self.invoice.button_draft()
        self.invoice.write(
            {"invoice_date": self.invoice.invoice_date - timedelta(days=1)}
        )
        self.invoice.action_post()
        self.assertEqual(old_name, self.invoice.name)

        self.invoice._constrains_date_sequence()
