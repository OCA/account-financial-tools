# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account_clearance_plan.tests.test_account_clearance_plan import (
    TestAccountClearancePlan,
)


@tagged("post_install", "-at_install")
class TestAccountClearancePlanBankPayment(TestAccountClearancePlan):
    @classmethod
    def get_default_groups(cls):
        return super().get_default_groups() | cls.env.ref(
            "account_payment_order.group_account_payment"
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.partner_a.id,
                "acc_number": "BE68539007547034",
            }
        )
        cls.mandate = cls.env["account.banking.mandate"].create(
            {
                "partner_bank_id": cls.partner_bank.id,
                "signature_date": fields.Date.today(),
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.mandate.validate()
        cls.payment_method_mandate = cls.env.ref(
            "account.account_payment_method_manual_in"
        ).copy({"code": "test_acp_mandate", "mandate_required": True})
        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Test inbound mode",
                "company_id": cls.company_data["company"].id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "bank_account_link": "variable",
            }
        )
        cls.payment_mode_mandate = cls.env["account.payment.mode"].create(
            {
                "name": "Test inbound mode with mandate",
                "company_id": cls.company_data["company"].id,
                "payment_method_id": cls.payment_method_mandate.id,
                "bank_account_link": "variable",
            }
        )
        cls.invoice.payment_mode_id = cls.payment_mode

    def test_confirm_clearance_plan_with_payment_mode(self):
        clearance_plan = self.create_and_fill_wizard().save()
        self.assertEqual(clearance_plan.payment_mode_id, self.payment_mode)
        res = clearance_plan.confirm_plan()
        move = self.env["account.move"].browse(res["res_id"])
        self.assertEqual(move.payment_mode_id, self.payment_mode)

    def test_confirm_clearance_plan_with_mandate(self):
        self.invoice.payment_mode_id = self.payment_mode_mandate
        self.assertEqual(self.invoice.mandate_id, self.mandate)
        clearance_plan = self.create_and_fill_wizard().save()
        self.assertEqual(clearance_plan.payment_mode_id, self.payment_mode_mandate)
        self.assertEqual(clearance_plan.mandate_id, self.mandate)
        res = clearance_plan.confirm_plan()
        move = self.env["account.move"].browse(res["res_id"])
        self.assertEqual(move.payment_mode_id, self.payment_mode_mandate)
        self.assertEqual(move.mandate_id, self.mandate)
