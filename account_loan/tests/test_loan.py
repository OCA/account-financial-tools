# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon

_logger = logging.getLogger(__name__)
try:
    import numpy_financial
except (OSError, ImportError) as err:
    _logger.error(err)


@tagged("post_install", "-at_install")
class TestLoan(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.company_02 = cls.env["res.company"].create({"name": "Auxiliar company"})
        cls.journal = cls.env["account.journal"].create(
            {
                "company_id": cls.company.id,
                "type": "purchase",
                "name": "Debts",
                "code": "DBT",
            }
        )
        cls.loan_account = cls.create_account(
            "DEP",
            "depreciation",
            "liability_current",
        )
        cls.payable_account = cls.create_account("PAY", "payable", "liability_payable")
        cls.asset_account = cls.create_account("ASSET", "asset", "liability_payable")
        cls.interests_account = cls.create_account("FEE", "Fees", "expense")
        cls.lt_loan_account = cls.create_account(
            "LTD",
            "Long term depreciation",
            "liability_non_current",
        )
        cls.partner = cls.env["res.partner"].create({"name": "Bank"})
        cls.product = cls.env["product.product"].create(
            {"name": "Payment", "type": "service"}
        )
        cls.interests_product = cls.env["product.product"].create(
            {"name": "Bank fee", "type": "service"}
        )

    def test_onchange(self):
        loan = self.env["account.loan"].create(
            {
                "name": "LOAN",
                "company_id": self.company.id,
                "journal_id": self.journal.id,
                "loan_type": "fixed-annuity",
                "loan_amount": 100,
                "rate": 1,
                "periods": 2,
                "short_term_loan_account_id": self.loan_account.id,
                "interest_expenses_account_id": self.interests_account.id,
                "product_id": self.product.id,
                "interests_product_id": self.interests_product.id,
                "partner_id": self.partner.id,
            }
        )
        loan_form = Form(loan)
        loan_form.is_leasing = True
        self.assertNotEqual(loan.journal_id, loan_form.journal_id)
        loan_form.company_id = self.company_02
        self.assertFalse(loan_form.interest_expenses_account_id)

    def test_partner_loans(self):
        self.assertFalse(self.partner.lended_loan_count)
        loan = self.create_loan("fixed-annuity", 500000, 1, 60)
        self.assertEqual(1, self.partner.lended_loan_count)
        action = self.partner.action_view_partner_lended_loans()
        self.assertEqual(loan, self.env[action["res_model"]].search(action["domain"]))

    @mute_logger("odoo.models.unlink")
    def test_round_on_end(self):
        loan = self.create_loan("fixed-annuity", 500000, 1, 60)
        loan.round_on_end = True
        loan.compute_lines()
        line_1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        for line in loan.line_ids:
            self.assertAlmostEqual(line_1.payment_amount, line.payment_amount, 2)
        loan.loan_type = "fixed-principal"
        loan.compute_lines()
        line_1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line_end = loan.line_ids.filtered(lambda r: r.sequence == 60)
        self.assertNotAlmostEqual(line_1.payment_amount, line_end.payment_amount, 2)
        loan.loan_type = "interest"
        loan.compute_lines()
        line_1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line_end = loan.line_ids.filtered(lambda r: r.sequence == 60)
        self.assertEqual(line_1.principal_amount, 0)
        self.assertEqual(line_end.principal_amount, 500000)

    @mute_logger("odoo.models.unlink")
    @freeze_time("2025-01-01")
    def test_increase_amount_validation(self):
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
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertGreater(line.long_term_principal_amount, 0)
        self.post(loan)
        self.assertTrue(loan.start_date)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.move_ids)
        wzd = self.env["account.loan.generate.wizard"].create({})
        action = wzd.run()
        self.assertTrue(action)
        self.assertFalse(wzd.run())
        self.assertTrue(line.move_ids)
        self.assertIn(line.move_ids.id, action["domain"][0][2])
        self.assertTrue(line.move_ids)
        self.assertEqual(line.move_ids.state, "posted")
        with self.assertRaises(UserError):
            self.env["account.loan.increase.amount"].with_context(
                default_loan_id=loan.id
            ).create(
                {
                    "amount": (amount - amount / periods) / 2,
                    "date": line.date + relativedelta(months=-1),
                }
            ).run()
        with self.assertRaises(UserError):
            self.env["account.loan.increase.amount"].with_context(
                default_loan_id=loan.id
            ).create({"amount": 0, "date": line.date}).run()
        with self.assertRaises(UserError):
            self.env["account.loan.increase.amount"].with_context(
                default_loan_id=loan.id
            ).create({"amount": -100, "date": line.date}).run()

    @mute_logger("odoo.models.unlink")
    @freeze_time("2025-01-01")
    def test_pay_amount_validation(self):
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
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertGreater(line.long_term_principal_amount, 0)
        self.post(loan)
        self.assertTrue(loan.start_date)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.move_ids)
        wzd = self.env["account.loan.generate.wizard"].create({})
        action = wzd.run()
        self.assertTrue(action)
        self.assertFalse(wzd.run())
        self.assertTrue(line.move_ids)
        self.assertIn(line.move_ids.id, action["domain"][0][2])
        self.assertTrue(line.move_ids)
        self.assertEqual(line.move_ids.state, "posted")
        with self.assertRaises(UserError):
            self.env["account.loan.pay.amount"].with_context(
                default_loan_id=loan.id
            ).create(
                {
                    "amount": (amount - amount / periods) / 2,
                    "fees": 100,
                    "date": line.date + relativedelta(months=-1),
                }
            ).run()
        with self.assertRaises(UserError):
            self.env["account.loan.pay.amount"].with_context(
                default_loan_id=loan.id
            ).create({"amount": amount, "fees": 100, "date": line.date}).run()
        with self.assertRaises(UserError):
            self.env["account.loan.pay.amount"].with_context(
                default_loan_id=loan.id
            ).create({"amount": 0, "fees": 100, "date": line.date}).run()
        with self.assertRaises(UserError):
            self.env["account.loan.pay.amount"].with_context(
                default_loan_id=loan.id
            ).create({"amount": -100, "fees": 100, "date": line.date}).run()

    @mute_logger("odoo.models.unlink")
    @freeze_time("2025-01-01")
    def test_increase_amount_loan(self):
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
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertGreater(line.long_term_principal_amount, 0)
        self.post(loan)
        self.assertTrue(loan.start_date)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.move_ids)
        wzd = self.env["account.loan.generate.wizard"].create({})
        action = wzd.run()
        self.assertTrue(action)
        self.assertFalse(wzd.run())
        self.assertTrue(line.move_ids)
        self.assertIn(line.move_ids.id, action["domain"][0][2])
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
        loan.is_leasing = True
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
                "date": fields.date.today() + relativedelta(days=1),
                "loan_type": "leasing",
            }
        )
        action = wzd.run()
        self.assertTrue(action)
        self.assertFalse(wzd.run())
        self.assertTrue(line.move_ids)
        self.assertIn(line.move_ids.id, action["domain"][0][2])
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
    def test_fixed_annuity_begin_loan(self):
        amount = 10000
        periods = 24
        loan = self.create_loan("fixed-annuity-begin", amount, 1, periods)
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertAlmostEqual(
            -numpy_financial.pmt(1 / 100 / 12, 24, 10000, when="begin"),
            line.payment_amount,
            2,
        )
        self.assertEqual(line.long_term_principal_amount, 0)
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertGreater(line.long_term_principal_amount, 0)
        self.post(loan)
        self.assertTrue(loan.start_date)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.move_ids)
        wzd = self.env["account.loan.generate.wizard"].create({})
        action = wzd.run()
        self.assertTrue(action)
        self.assertFalse(wzd.run())
        self.assertTrue(line.move_ids)
        self.assertIn(line.move_ids.id, action["domain"][0][2])
        self.assertTrue(line.move_ids)
        self.assertEqual(line.move_ids.state, "posted")
        loan.rate = 2
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertAlmostEqual(
            -numpy_financial.pmt(1 / 100 / 12, periods, amount, when="begin"),
            line.payment_amount,
            2,
        )
        line = loan.line_ids.filtered(lambda r: r.sequence == 2)
        self.assertAlmostEqual(
            -numpy_financial.pmt(
                2 / 100 / 12, periods - 1, line.pending_principal_amount, when="begin"
            ),
            line.payment_amount,
            2,
        )
        line = loan.line_ids.filtered(lambda r: r.sequence == 3)
        with self.assertRaises(UserError):
            line.view_process_values()

    @mute_logger("odoo.models.unlink")
    @freeze_time("2025-01-01")
    def test_fixed_annuity_loan(self):
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
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertGreater(line.long_term_principal_amount, 0)
        self.post(loan)
        self.assertTrue(loan.start_date)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertTrue(line)
        self.assertFalse(line.move_ids)
        wzd = self.env["account.loan.generate.wizard"].create({})
        action = wzd.run()
        self.assertTrue(action)
        self.assertFalse(wzd.run())
        self.assertTrue(line.move_ids)
        self.assertIn(line.move_ids.id, action["domain"][0][2])
        self.assertTrue(line.move_ids)
        self.assertEqual(line.move_ids.state, "posted")
        loan.rate = 2
        loan.compute_lines()
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        self.assertAlmostEqual(
            -numpy_financial.pmt(1 / 100 / 12, periods, amount), line.payment_amount, 2
        )
        line = loan.line_ids.filtered(lambda r: r.sequence == 2)
        self.assertAlmostEqual(
            -numpy_financial.pmt(
                2 / 100 / 12, periods - 1, line.pending_principal_amount
            ),
            line.payment_amount,
            2,
        )
        line = loan.line_ids.filtered(lambda r: r.sequence == 3)
        with self.assertRaises(UserError):
            line.view_process_values()

    @mute_logger("odoo.models.unlink")
    @freeze_time("2025-01-01")
    def test_fixed_principal_loan_leasing(self):
        amount = 24000
        periods = 24
        loan = self.create_loan("fixed-principal", amount, 1, periods)
        self.partner.property_account_payable_id = self.payable_account
        self.assertEqual(loan.journal_type, "general")
        loan.is_leasing = True
        loan.post_invoice = False
        self.assertEqual(loan.journal_type, "purchase")
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
        self.assertFalse(line.has_invoices)
        self.assertFalse(line.has_moves)
        action = (
            self.env["account.loan.generate.wizard"]
            .create(
                {
                    "date": fields.date.today() + relativedelta(days=1),
                    "loan_type": "leasing",
                }
            )
            .run()
        )
        self.assertTrue(line.has_invoices)
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
        self.assertEqual(loan.journal_type, "general")
        loan.is_leasing = True
        self.assertEqual(loan.journal_type, "purchase")
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
        self.assertFalse(line.has_invoices)
        self.assertFalse(line.has_moves)
        self.env["account.loan.generate.wizard"].create(
            {"date": fields.date.today(), "loan_type": "leasing"}
        ).run()
        self.assertTrue(line.has_invoices)
        self.assertTrue(line.has_moves)

    @mute_logger("odoo.models.unlink")
    def test_interests_on_end_loan(self):
        amount = 10000
        periods = 10
        loan = self.create_loan("interest", amount, 1, periods)
        loan.payment_on_first_period = False
        loan.start_date = fields.Date.today()
        loan.rate_type = "ear"
        loan.compute_lines()
        self.assertTrue(loan.line_ids)
        self.assertEqual(len(loan.line_ids), periods)
        self.assertEqual(0, loan.line_ids[0].principal_amount)
        self.assertEqual(
            amount,
            loan.line_ids.filtered(lambda r: r.sequence == periods).principal_amount,
        )
        self.post(loan)
        self.assertEqual(loan.payment_amount, 0)
        self.assertEqual(loan.interests_amount, 0)
        self.assertEqual(loan.pending_principal_amount, amount)
        self.assertFalse(loan.line_ids.filtered(lambda r: r.date <= loan.start_date))
        for line in loan.line_ids:
            self.assertEqual(loan.state, "posted")
            line.view_process_values()
            self.assertTrue(line.move_ids)
            self.assertEqual(line.move_ids.state, "posted")
        self.assertEqual(loan.state, "closed")
        loan.invalidate_recordset()
        self.assertEqual(loan.payment_amount - loan.interests_amount, amount)
        self.assertEqual(loan.pending_principal_amount, 0)

    @mute_logger("odoo.models.unlink")
    def test_cancel_loan(self):
        amount = 10000
        periods = 10
        loan = self.create_loan("fixed-annuity", amount, 1, periods)
        self.post(loan)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line.view_process_values()
        self.assertTrue(line.move_ids)
        self.assertEqual(line.move_ids.state, "posted")
        pay = self.env["account.loan.pay.amount"].create(
            {"loan_id": loan.id, "amount": 0, "fees": 100, "date": line.date}
        )
        pay.cancel_loan = True
        pay._onchange_cancel_loan()
        self.assertEqual(pay.amount, line.final_pending_principal_amount)
        pay.run()
        self.assertEqual(loan.state, "cancelled")

    def post(self, loan):
        self.assertFalse(loan.move_ids)
        post = (
            self.env["account.loan.post"]
            .with_context(default_loan_id=loan.id)
            .create({})
        )
        post.run()
        self.assertTrue(loan.move_ids)
        with self.assertRaises(UserError):
            post.run()

    @classmethod
    def create_account(cls, code, name, account_type):
        return cls.env["account.account"].create(
            {
                "company_id": cls.company.id,
                "name": name,
                "code": code,
                "account_type": account_type,
                "reconcile": True,
            }
        )

    def create_loan(self, type_loan, amount, rate, periods):
        loan = self.env["account.loan"].create(
            {
                "journal_id": self.journal.id,
                "rate_type": "napr",
                "loan_type": type_loan,
                "loan_amount": amount,
                "payment_on_first_period": True,
                "rate": rate,
                "periods": periods,
                "leased_asset_account_id": self.asset_account.id,
                "short_term_loan_account_id": self.loan_account.id,
                "interest_expenses_account_id": self.interests_account.id,
                "product_id": self.product.id,
                "interests_product_id": self.interests_product.id,
                "partner_id": self.partner.id,
            }
        )
        loan.compute_lines()
        return loan
