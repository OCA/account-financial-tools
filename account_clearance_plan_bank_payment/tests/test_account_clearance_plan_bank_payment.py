# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form
from odoo.addons.account_clearance_plan.tests.test_account_clearance_plan import (
    TestAccountClearancePlanBase,
)

from datetime import datetime, timedelta


class TestAccountClearancePlanBankPayment(TestAccountClearancePlanBase):
    def setUp(self):
        super(TestAccountClearancePlanBankPayment, self).setUp()
        self.partner_bank = self.env.ref("account_payment_mode.main_company_iban")
        self.partner_bank.write({"partner_id": self.partner.id})
        self.mandate = self.env["account.banking.mandate"].create(
            {
                "partner_bank_id": self.partner_bank.id,
                "signature_date": "2015-01-01",
                "company_id": self.company.id,
            }
        )
        self.mandate.validate()
        self.payment_method_mandate_manual_in = self.payment_method_manual_in.copy(
            default={"code": "test_acp", "mandate_required": True}
        )
        self.payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "Test payment mode",
                "company_id": self.company.id,
                "payment_method_id": self.payment_method_mandate_manual_in.id,
                "bank_account_link": "variable",
            }
        )
        self.invoice.write({"payment_mode_id": self.payment_mode.id})

    def create_and_fill_wizard(self):
        clearance_plan_wizard = Form(
            self.env["account.clearance.plan"].with_context(self.invoice_ctx)
        )
        i = 1
        while i <= 4:
            with clearance_plan_wizard.clearance_plan_line_ids.new() as line:
                line.amount = 200.0
                line.date_maturity = (datetime.now() + timedelta(days=30 * i)).strftime(
                    "%Y-%m-%d"
                )
                line.mandate_id = self.mandate
            i += 1
        return clearance_plan_wizard

    def test_confirm_clearance_plan(self):
        clearance_plan = self.create_and_fill_wizard().save()
        res = clearance_plan.confirm_plan()
        move = self.env["account.move"].browse(res["res_id"])
        for line in clearance_plan.clearance_plan_line_ids:
            self.assertTrue(
                move.line_ids.filtered(
                    lambda l: l.debit == line.amount
                    and l.date_maturity == line.date_maturity
                    and l.payment_mode_id == line.payment_mode_id
                    and l.mandate_id == line.mandate_id
                )
            )
