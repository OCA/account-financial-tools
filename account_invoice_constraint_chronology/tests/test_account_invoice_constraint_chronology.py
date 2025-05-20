# Copyright 2015-2019 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2021 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import time
from datetime import date, timedelta

from freezegun import freeze_time

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


# in order to avoid a raise caused by the sequence mixin we must ensure
# that all dates are in the same year, hence we freeze the date
# in the middle of the year
@freeze_time(f"{date.today().year}-07-01")
class TestAccountInvoiceConstraintChronology(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        cls.partner_12 = cls.env.ref("base.res_partner_12")
        cls.today = fields.Date.today()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.tomorrow = cls.today + timedelta(days=1)
        cls.AccountJournal = cls.env["account.journal"]
        cls.sale_journal = cls.AccountJournal.create(
            {
                "name": "Sale journal",
                "code": "SALE",
                "type": "sale",
                "check_chronology": True,
            }
        )

        cls.ProductProduct = cls.env["product.product"]
        cls.AccountChartTemplate = cls.env["account.chart.template"]
        cls.product = cls.ProductProduct.create({"name": "Product"})
        cls.AccountMove = cls.env["account.move"]
        with Form(
            cls.AccountMove.with_context(default_move_type="out_invoice")
        ) as invoice_form:
            invoice_form.invoice_date = cls.today
            invoice_form.partner_id = cls.partner_2
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = cls.product
            cls.invoice_1 = invoice_form.save()
        cls.invoice_1.update({"journal_id": cls.sale_journal})
        cls.invoice_2 = cls.invoice_1.copy()
        cls.AccountMoveReversal = cls.env["account.move.reversal"]

    def test_journal_type_change(self):
        self.assertTrue(self.sale_journal.check_chronology)

        with Form(self.sale_journal) as form:
            form.type = "general"
        self.assertFalse(self.sale_journal.check_chronology)

        with Form(self.sale_journal) as form:
            form.type = "sale"
        self.assertFalse(self.sale_journal.check_chronology)

        with Form(self.sale_journal) as form:
            form.check_chronology = True
        self.assertTrue(self.sale_journal.check_chronology)

    def test_invoice_draft(self):
        self.invoice_1.invoice_date = self.yesterday
        self.invoice_2.invoice_date = self.today
        with self.assertRaises(UserError):
            self.invoice_2.action_post()

    def test_invoice_draft_nocheck(self):
        self.invoice_1.invoice_date = self.yesterday
        self.invoice_2.invoice_date = self.today
        self.sale_journal.check_chronology = False
        self.invoice_2.action_post()

    def test_invoice_validate(self):
        self.invoice_1.invoice_date = self.tomorrow
        self.invoice_1.action_post()
        self.invoice_2.invoice_date = self.today
        with self.assertRaises(UserError):
            self.invoice_2.action_post()

    def test_invoice_without_date(self):
        self.invoice_1.invoice_date = self.yesterday
        self.invoice_2.invoice_date = False
        with self.assertRaises(UserError):
            self.invoice_2.action_post()

    def test_invoice_refund_before(self):
        self.invoice_1.invoice_date = self.tomorrow
        self.invoice_1.action_post()
        refund = (
            self.AccountMoveReversal.with_context(
                active_model="account.move",
                active_ids=self.invoice_1.ids,
            )
            .create(
                {
                    "date": self.today,
                    "reason": "no reason",
                    "journal_id": self.invoice_1.journal_id.id,
                }
            )
            .reverse_moves()
        )
        refund = self.AccountMove.browse(refund["res_id"])
        refund.action_post()

    def test_invoice_refund_before_same_sequence(self):
        self.sale_journal.refund_sequence = False
        self.invoice_1.invoice_date = self.tomorrow
        self.invoice_1.action_post()
        refund = (
            self.AccountMoveReversal.with_context(
                active_model="account.move",
                active_ids=self.invoice_1.ids,
            )
            .create(
                {
                    "date": self.today,
                    "reason": "no reason",
                    "journal_id": self.invoice_1.journal_id.id,
                }
            )
            .reverse_moves()
        )
        refund = self.AccountMove.browse(refund["res_id"])
        with self.assertRaises(UserError):
            refund.action_post()

    def test_invoice_higher_number(self):
        self.invoice_1.invoice_date = self.yesterday
        self.invoice_1.action_post()
        self.invoice_1.button_draft()
        self.invoice_1.invoice_date = False

        self.invoice_2.invoice_date = self.today
        self.invoice_2.action_post()

        self.invoice_1.invoice_date = self.tomorrow
        with self.assertRaisesRegex(UserError, "higher number"):
            self.invoice_1.action_post()

    def test_modify_validated_past_invoice(self):
        """We've got an invoice from yesterday that we need to modify but new ones
        have been posted since. As the invoice already has a name, we should be able
        to validate it"""
        self.invoice_1.invoice_date = self.yesterday
        self.invoice_1.action_post()
        self.invoice_2.invoice_date = self.today
        self.invoice_2.action_post()
        self.invoice_1.button_cancel()
        self.invoice_1.button_draft()
        self.invoice_1.action_post()
        self.invoice_1_5 = self.invoice_1.copy()
        self.invoice_1_5.invoice_date = self.yesterday
        with self.assertRaises(UserError):
            self.invoice_1_5.action_post()

    def test_modify_invoice_date_validated_past_invoice(self):
        # INV5 YYYYMM20 posted
        # INV4 YYYYMM15 posted
        # INV3 YYYYMM10 posted
        # INV2 YYYYMM05 posted
        # INV1 YYYYMM01 posted
        # if we pass INV3 to draft and change the date to YYYYYMM15 or YYYYYMM05
        # it should be able to validate, but if we change the date
        # higher than YYYYYMM15 or lower than YYYYYMM05
        # it should not be able to validate.

        # FIX conflict between 'freeze_time' and account module demo data
        demo_invoice_1 = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_2.id,
                "invoice_date": time.strftime("%Y-%m-01"),
                "delivery_date": time.strftime("%Y-%m-01"),
                "invoice_line_ids": [
                    Command.create({"product_id": self.product.id, "quantity": 5}),
                ],
            }
        )
        demo_invoice_2 = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_2.id,
                "invoice_user_id": False,
                "invoice_date": (fields.Date.today() + timedelta(days=-2)).strftime(
                    "%Y-%m-%d"
                ),
                "delivery_date": (fields.Date.today() + timedelta(days=-2)).strftime(
                    "%Y-%m-%d"
                ),
                "invoice_line_ids": [
                    Command.create({"product_id": self.product.id, "quantity": 5}),
                ],
            }
        )
        demo_invoice_3 = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_2.id,
                "invoice_user_id": False,
                "invoice_date": (fields.Date.today() + timedelta(days=-3)).strftime(
                    "%Y-%m-%d"
                ),
                "delivery_date": (fields.Date.today() + timedelta(days=-3)).strftime(
                    "%Y-%m-%d"
                ),
                "invoice_line_ids": [
                    Command.create({"product_id": self.product.id, "quantity": 5}),
                ],
            }
        )
        demo_invoice_followup = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_2.id,
                "invoice_date": (fields.Date.today() + timedelta(days=-15)).strftime(
                    "%Y-%m-%d"
                ),
                "delivery_date": (fields.Date.today() + timedelta(days=-15)).strftime(
                    "%Y-%m-%d"
                ),
                "invoice_line_ids": [
                    Command.create({"product_id": self.product.id, "quantity": 5}),
                ],
            }
        )
        demo_invoice_5 = self.AccountMove.create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_2.id,
                "invoice_date": time.strftime("%Y-%m-01"),
                "delivery_date": time.strftime("%Y-%m-01"),
                "invoice_line_ids": [
                    Command.create({"product_id": self.product.id, "quantity": 5}),
                ],
            }
        )
        demo_invoice_1.action_post()
        demo_invoice_2.action_post()
        demo_invoice_3.action_post()
        demo_invoice_5.action_post()
        demo_invoice_followup.action_post()
        demo_invoice_1.button_draft()
        demo_invoice_2.button_draft()
        demo_invoice_3.button_draft()
        demo_invoice_5.button_draft()
        demo_invoice_followup.button_draft()
        demo_invoice_1.write(
            {"name": False, "invoice_date": date.today().replace(day=1)}
        )
        demo_invoice_2.write(
            {"name": False, "invoice_date": date.today().replace(day=1)}
        )
        demo_invoice_3.write(
            {"name": False, "invoice_date": date.today().replace(day=1)}
        )
        demo_invoice_5.write(
            {"name": False, "invoice_date": date.today().replace(day=1)}
        )
        demo_invoice_followup.write(
            {"name": False, "invoice_date": date.today().replace(day=1)}
        )
        after_5_days = self.today + timedelta(days=5)
        after_10_days = self.today + timedelta(days=10)
        after_15_days = self.today + timedelta(days=15)
        after_20_days = self.today + timedelta(days=20)
        after_25_days = self.today + timedelta(days=25)

        self.invoice_1.action_post()

        self.invoice_1_a_5 = self.invoice_1.copy()
        self.invoice_1_a_5.invoice_date = after_5_days
        self.invoice_1_a_5.action_post()
        self.invoice_1_a_10 = self.invoice_1.copy()
        self.invoice_1_a_10.invoice_date = after_10_days
        self.invoice_1_a_10.action_post()
        self.invoice_1_a_15 = self.invoice_1.copy()
        self.invoice_1_a_15.invoice_date = after_15_days
        self.invoice_1_a_15.action_post()
        self.invoice_1_a_20 = self.invoice_1.copy()
        self.invoice_1_a_20.invoice_date = after_20_days
        self.invoice_1_a_20.action_post()
        self.invoice_1_a_25 = self.invoice_1.copy()
        self.invoice_1_a_25.invoice_date = after_25_days
        self.invoice_1_a_25.action_post()

        self.invoice_1_a_15.button_cancel()
        self.invoice_1_a_15.button_draft()
        self.invoice_1_a_15.invoice_date = after_10_days
        self.invoice_1_a_15.action_post()

        self.invoice_1_a_15.button_cancel()
        self.invoice_1_a_15.button_draft()
        self.invoice_1_a_15.invoice_date = after_10_days - timedelta(days=1)
        with self.assertRaisesRegex(
            UserError,
            (
                f"Chronology conflict: Invoice {self.invoice_1_a_15.name} cannot be "
                f"before invoice {self.invoice_1_a_10.name}."
            ),
        ):
            self.invoice_1_a_15.action_post()
        self.invoice_1_a_15.button_cancel()
        self.invoice_1_a_15.button_draft()
        self.invoice_1_a_15.invoice_date = after_20_days
        self.invoice_1_a_15.action_post()
        self.invoice_1_a_15.button_cancel()
        self.invoice_1_a_15.button_draft()
        self.invoice_1_a_15.invoice_date = after_20_days + timedelta(days=1)
        with self.assertRaisesRegex(
            UserError,
            (
                f"Chronology conflict: Invoice {self.invoice_1_a_15.name} cannot be"
                f" after invoice {self.invoice_1_a_20.name}."
            ),
        ):
            self.invoice_1_a_15.action_post()

    def test_post_invoice_with_name(self):
        assert self.invoice_1.state == "draft"
        invoice2 = self.invoice_1.copy()
        invoice2.invoice_date = self.invoice_1.invoice_date + timedelta(days=1)
        self.invoice_1.action_post()
