# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.exceptions import UserError

from .common import TestAccountFinancialDiscountCommon


class TestAccountFinancialDiscountManualPayment(TestAccountFinancialDiscountCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice1 = cls.init_invoice(
            cls.partner,
            "in_invoice",
            payment_term=cls.payment_term,
            invoice_date="2019-04-01",
            invoice_date_due="2019-05-01",
        )
        cls.init_invoice_line(cls.invoice1, 1.0, 1000.0)

    def test_payment_term_write(self):
        self.assertEqual(self.payment_term.percent_discount, 10)
        self.payment_term.write({"percent_discount": 20})
        self.assertEqual(self.payment_term.percent_discount, 20)
        self.invoice1.action_post()
        with self.assertRaises(UserError):
            self.payment_term.write({"percent_discount": 10})
