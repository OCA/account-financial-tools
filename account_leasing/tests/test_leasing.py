# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.account_loan.tests.common import LoanCommon

_logger = logging.getLogger(__name__)
try:
    import numpy_financial
except (OSError, ImportError) as err:
    _logger.error(err)


@tagged("post_install", "-at_install")
class TestLeasing(LoanCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_account = cls.create_account("ASSET", "asset", "liability_payable")
        cls.product = cls.env["product.product"].create(
            {"name": "Payment", "type": "service"}
        )
        cls.interests_product = cls.env["product.product"].create(
            {"name": "Bank fee", "type": "service"}
        )

    def _prepare_loan_data(self, type_loan, amount, rate, period, loan_type="leasing"):
        data = super()._prepare_loan_data(
            type_loan, amount, rate, period, loan_type=loan_type
        )
        data.update(
            {
                "leased_asset_account_id": self.asset_account.id,
                "product_id": self.product.id,
                "interests_product_id": self.interests_product.id,
                "loan_type": loan_type,
            }
        )
        return data

    def test_constrains_leasing_must_have_postive_amount(self):
        with self.assertRaisesRegex(
            ValidationError, "Leasing type must have postive amount or change the type"
        ):
            self.create_loan("fixed-annuity", -4000, 1, 10, loan_type="leasing")

    def test_onchange(self):
        loan = self.create_loan("fixed-annuity", 500000, 1, 60, loan_type="loan")
        self.assertNotEqual(loan.journal_id.type, "purchase")
        with Form(loan) as loan_form:
            loan_form.loan_type = "leasing"
            self.assertNotEqual(loan.journal_id, loan_form.journal_id)
        self.assertEqual(loan.journal_id.type, "purchase")
        loan_form.company_id = self.company_02
        self.assertFalse(loan_form.interest_expenses_account_id)

    def test_partner_loans(self):
        self.assertFalse(self.partner.lended_loan_count)
        loan = self.create_loan("fixed-annuity", 500000, 1, 60)
        self.assertEqual(1, self.partner.lended_loan_count)
        action = self.partner.action_view_partner_lended_loans()
        self.assertEqual(loan, self.env[action["res_model"]].search(action["domain"]))

    @mute_logger("odoo.models.unlink")
    @freeze_time("2025-01-01")
    def test_increase_amount_leasing(self):
        amount = 10000
        periods = 24
        loan = self.create_loan("fixed-annuity", amount, 1, periods)
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertAlmostEqual(
            -numpy_financial.pmt(1 / 100 / 12, 24, 10000), line.payment_amount, 2
        )
        self.assertEqual(line.long_term_principal_amount, 0)
        loan.loan_type = "leasing"
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertGreater(line.long_term_principal_amount, 0)
        self.post(loan)
        self.assertTrue(loan.start_date)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.move_ids)
        wzd = self.env["account.loan.generate.wizard"].create(
            {
                "date": fields.Date.today() + relativedelta(days=1),
                "loan_type": "leasing",
            }
        )
        action = wzd.run()
        self.assertTrue(action)
        self.assertFalse(wzd.run())
        self.assertTrue(line.move_ids)
        self.assertEqual(list(action["domain"]), [("id", "in", line.move_ids.ids)])
        self.assertTrue(line.move_ids)
        self.assertEqual(line.move_ids.state, "posted")
        pending_principal_amount = loan.pending_principal_amount
        action = (
            self.env["account.loan.increase.amount"]
            .with_context(default_loan_id=loan.id)
            .create(
                {
                    "amount": 1000,
                    "date": line.date,
                }
            )
            .run()
        )
        new_move = self.env[action["res_model"]].search(action["domain"])
        new_move.ensure_one()
        self.assertFalse(new_move.is_invoice())
        self.assertEqual(loan, new_move.loan_id)
        self.assertEqual(loan.pending_principal_amount, pending_principal_amount + 1000)

    @mute_logger("odoo.models.unlink")
    @freeze_time("2025-01-01")
    def test_fixed_principal_loan_leasing(self):
        amount = 24000
        periods = 24
        loan = self.create_loan("fixed-principal", amount, 1, periods)
        self.partner.property_account_payable_id = self.payable_account
        loan.post_invoice = False
        self.assertEqual(loan.journal_id.type, "purchase")
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.rate_type = "real"
        loan.compute_lines()
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertEqual(amount / periods, line.principal_amount)
        self.assertEqual(amount / periods, line.long_term_principal_amount)
        self.post(loan)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.has_moves)
        action = (
            self.env["account.loan.generate.wizard"]
            .create(
                {
                    "date": fields.Date.today() + relativedelta(days=1),
                    "loan_type": "leasing",
                }
            )
            .run()
        )
        self.assertTrue(line.has_moves)
        self.assertEqual(
            line.move_ids, self.env[action["res_model"]].search(action["domain"])
        )
        loan.invalidate_recordset()
        with self.assertRaises(UserError):
            self.env["account.loan.pay.amount"].create(
                {
                    "loan_id": loan.id,
                    "amount": (amount - amount / periods) / 2,
                    "fees": 100,
                    "date": loan.line_ids.filtered(lambda r: r.sequence == 2).date,
                }
            ).run()
        with self.assertRaises(UserError):
            self.env["account.loan.pay.amount"].create(
                {
                    "loan_id": loan.id,
                    "amount": (amount - amount / periods) / 2,
                    "fees": 100,
                    "date": loan.line_ids.filtered(lambda r: r.sequence == 1).date
                    + relativedelta(months=-1),
                }
            ).run()
        self.assertTrue(line.move_ids)
        self.assertTrue(line.move_ids.filtered(lambda r: r.is_invoice()))
        self.assertTrue(line.move_ids.filtered(lambda r: not r.is_invoice()))
        self.assertTrue(all([m.state == "draft" for m in line.move_ids]))
        self.assertTrue(line.has_moves)
        line.move_ids.action_post()
        self.assertTrue(all([m.state == "posted" for m in line.move_ids]))
        for move in line.move_ids:
            self.assertIn(
                move,
                self.env["account.move"].search(loan.view_account_moves()["domain"]),
            )
        for move in line.move_ids.filtered(lambda r: r.is_invoice()):
            self.assertIn(
                move,
                self.env["account.move"].search(loan.view_account_invoices()["domain"]),
            )
        with self.assertRaises(UserError):
            self.env["account.loan.pay.amount"].create(
                {
                    "loan_id": loan.id,
                    "amount": (amount - amount / periods) / 2,
                    "fees": 100,
                    "date": loan.line_ids.filtered(
                        lambda r: r.sequence == periods
                    ).date,
                }
            ).run()
        self.env["account.loan.pay.amount"].create(
            {
                "loan_id": loan.id,
                "amount": (amount - amount / periods) / 2,
                "date": line.date,
                "fees": 100,
            }
        ).run()
        line = loan.line_ids.filtered(lambda r: r.sequence == 2)
        self.assertEqual(loan.periods, periods + 1)
        self.assertAlmostEqual(
            line.principal_amount, (amount - amount / periods) / 2, 2
        )
        line = loan.line_ids.filtered(lambda r: r.sequence == 3)
        self.assertEqual(amount / periods / 2, line.principal_amount)
        line = loan.line_ids.filtered(lambda r: r.sequence == 4)
        with self.assertRaises(UserError):
            line.view_process_values()

    @mute_logger("odoo.models.unlink")
    @freeze_time("2025-01-01")
    def test_fixed_principal_loan_auto_post_leasing(self):
        amount = 24000
        periods = 24
        loan = self.create_loan("fixed-principal", amount, 1, periods)
        self.partner.property_account_payable_id = self.payable_account
        self.assertEqual(loan.journal_id.type, "purchase")
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.rate_type = "real"
        loan.compute_lines()
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertEqual(amount / periods, line.principal_amount)
        self.assertEqual(amount / periods, line.long_term_principal_amount)
        self.post(loan)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.has_moves)
        self.env["account.loan.generate.wizard"].create(
            {"date": fields.Date.today(), "loan_type": "leasing"}
        ).run()
        self.assertTrue(line.has_moves)
