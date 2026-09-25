# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from unittest.mock import patch

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
class TestLoan(LoanCommon):
    def test_constrains_loan_must_have_postive_amount(self):
        with self.assertRaisesRegex(
            ValidationError, "Loan type must have postive amount or change the type"
        ):
            self.create_loan("fixed-annuity", -4000, 1, 10, loan_type="loan")

    def test_constrains_borrow_must_have_negative_amount(self):
        with self.assertRaisesRegex(
            ValidationError, "Borrow type must have negative amount or change the type"
        ):
            self.create_loan("fixed-annuity", 4000, 1, 10, loan_type="borrow")

    def test_journal_type_constrains(self):
        loan = self.create_loan("fixed-annuity", 4000, 1, 10, loan_type="loan")
        with self.assertRaisesRegex(
            ValidationError,
            r"The current journal Debts type: purchase \(company My Company\) "
            r"is not allowed for this type loan",
        ):
            loan.journal_id = self.journal

    def test_partner_loans(self):
        self.assertFalse(self.partner.lended_loan_count)
        loan = self.create_loan("fixed-annuity", 500000, 1, 60)
        self.assertEqual(1, self.partner.lended_loan_count)
        action = self.partner.action_view_partner_lended_loans()
        self.assertEqual(loan, self.env[action["res_model"]].search(action["domain"]))

    @mute_logger("odoo.models.unlink")
    @freeze_time("2025-01-31")
    def test_loan_lines_custom_day_01(self):
        loan = self.create_loan("fixed-annuity", 500000, 1, 60)
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.compute_lines()
        dates_by_sequence = {}
        for line in loan.line_ids:
            dates_by_sequence[line.sequence] = line.date
        self.assertEqual(dates_by_sequence[1], fields.Date.from_string("2025-01-31"))
        self.assertEqual(dates_by_sequence[2], fields.Date.from_string("2025-02-28"))
        self.assertEqual(dates_by_sequence[3], fields.Date.from_string("2025-03-31"))
        self.assertEqual(dates_by_sequence[4], fields.Date.from_string("2025-04-30"))
        self.assertEqual(dates_by_sequence[5], fields.Date.from_string("2025-05-31"))
        self.assertEqual(dates_by_sequence[6], fields.Date.from_string("2025-06-30"))
        self.assertEqual(dates_by_sequence[7], fields.Date.from_string("2025-07-31"))
        self.assertEqual(dates_by_sequence[8], fields.Date.from_string("2025-08-31"))
        self.assertEqual(dates_by_sequence[9], fields.Date.from_string("2025-09-30"))
        self.assertEqual(dates_by_sequence[10], fields.Date.from_string("2025-10-31"))
        self.assertEqual(dates_by_sequence[11], fields.Date.from_string("2025-11-30"))
        self.assertEqual(dates_by_sequence[12], fields.Date.from_string("2025-12-31"))
        self.assertEqual(dates_by_sequence[13], fields.Date.from_string("2026-01-31"))
        line_1 = loan.line_ids.filtered(lambda x: x.sequence == 1)
        self.assertEqual(line_1.long_term_pending_principal_amount, 401989.15)
        self.assertAlmostEqual(line_1.long_term_principal_amount, 8211.88)
        line_2 = loan.line_ids.filtered(lambda x: x.sequence == 2)
        self.assertEqual(line_2.long_term_pending_principal_amount, 393777.27)
        line_13 = loan.line_ids.filtered(lambda x: x.sequence == 13)
        self.assertEqual(line_13.pending_principal_amount, 401989.15)
        self.assertEqual(
            line_1.long_term_pending_principal_amount, line_13.pending_principal_amount
        )

    @mute_logger("odoo.models.unlink")
    @freeze_time("2024-12-31")
    def test_loan_lines_custom_day_02(self):
        loan = self.create_loan("fixed-annuity", 500000, 1, 60)
        loan.long_term_loan_account_id = self.lt_loan_account
        loan.payment_on_first_period = False
        loan.compute_lines()
        dates_by_sequence = {}
        for line in loan.line_ids:
            dates_by_sequence[line.sequence] = line.date
        self.assertEqual(dates_by_sequence[1], fields.Date.from_string("2025-01-31"))
        self.assertEqual(dates_by_sequence[2], fields.Date.from_string("2025-02-28"))
        self.assertEqual(dates_by_sequence[3], fields.Date.from_string("2025-03-31"))
        self.assertEqual(dates_by_sequence[4], fields.Date.from_string("2025-04-30"))
        self.assertEqual(dates_by_sequence[5], fields.Date.from_string("2025-05-31"))
        self.assertEqual(dates_by_sequence[6], fields.Date.from_string("2025-06-30"))
        self.assertEqual(dates_by_sequence[7], fields.Date.from_string("2025-07-31"))
        self.assertEqual(dates_by_sequence[8], fields.Date.from_string("2025-08-31"))
        self.assertEqual(dates_by_sequence[9], fields.Date.from_string("2025-09-30"))
        self.assertEqual(dates_by_sequence[10], fields.Date.from_string("2025-10-31"))
        self.assertEqual(dates_by_sequence[11], fields.Date.from_string("2025-11-30"))
        self.assertEqual(dates_by_sequence[12], fields.Date.from_string("2025-12-31"))
        self.assertEqual(dates_by_sequence[13], fields.Date.from_string("2026-01-31"))
        line_1 = loan.line_ids.filtered(lambda x: x.sequence == 1)
        self.assertEqual(line_1.long_term_pending_principal_amount, 401989.15)
        self.assertAlmostEqual(line_1.long_term_principal_amount, 8211.88)
        line_2 = loan.line_ids.filtered(lambda x: x.sequence == 2)
        self.assertEqual(line_2.long_term_pending_principal_amount, 393777.27)
        line_13 = loan.line_ids.filtered(lambda x: x.sequence == 13)
        self.assertEqual(line_13.pending_principal_amount, 401989.15)
        self.assertEqual(
            line_1.long_term_pending_principal_amount, line_13.pending_principal_amount
        )

    @mute_logger("odoo.models.unlink")
    def test_round_on_end(self):
        loan = self.create_loan("fixed-annuity", 500000, 1, 60)
        loan.round_on_end = True
        loan.compute_lines()
        line_1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        for line in loan.line_ids:
            self.assertAlmostEqual(line_1.payment_amount, line.payment_amount, 2)
        loan.loan_method = "fixed-principal"
        loan.compute_lines()
        line_1 = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line_end = loan.line_ids.filtered(lambda r: r.sequence == 60)
        self.assertNotAlmostEqual(line_1.payment_amount, line_end.payment_amount, 2)
        loan.loan_method = "interest"
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

        self.assertEqual(list(action["domain"]), [("id", "in", line.move_ids.ids)])

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
        self.assertEqual(list(action["domain"]), [("id", "in", line.move_ids.ids)])
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
        self.assertEqual(list(action["domain"]), [("id", "in", line.move_ids.ids)])
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
        self.assertEqual(list(action["domain"]), [("id", "in", line.move_ids.ids)])
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
    def test_interests_on_end_loan(self):
        amount = 10000
        periods = 10
        loan = self.create_loan("interest", amount, 1, periods)
        self.assertEqual(loan.loan_type, "loan")
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

    def test_negative_loan(self):
        # Check that negatives amounts don't give an error
        loan = self.create_loan("fixed-annuity", -4000, 1, 10, loan_type="borrow")
        self.post(loan)
        loan.line_ids[0].view_process_values()

    @mute_logger("odoo.models.unlink")
    def test_cancel_loan(self):
        amount = 10000
        periods = 10
        loan = self.create_loan("fixed-annuity", amount, 1, periods)
        self.post(loan)
        with self.assertRaisesRegex(
            UserError,
            "It is only possible to change to draft if the status is "
            "cancelled or posted and there are no account moves.",
        ):
            loan.button_draft()
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
        with self.assertRaisesRegex(
            UserError,
            "It is only possible to change to draft if the status is "
            "cancelled or posted and there are no account moves.",
        ):
            loan.button_draft()
        loan.move_ids.button_draft()
        loan.move_ids.unlink()
        loan.button_draft()
        self.assertEqual(loan.state, "draft")

    def test_loan_onchange_rate_posted_warning(self):
        loan = self.create_loan("fixed-annuity", 10000, 1, 12)
        self.post(loan)
        loan.rate = 2.0
        res = loan._onchange_rate_warning()
        self.assertTrue(res.get("warning"))
        self.assertEqual(res["warning"]["title"], "Rate Change")

    def test_loan_fixed_amount_computation(self):
        """Testing _compute_fixed_amount"""
        loan = self.create_loan("fixed-annuity-begin", 10000, 1, 12)
        self.assertNotEqual(loan.fixed_amount, 0.0)
        with Form(loan) as loan_form:
            loan_form.loan_method = "interest"
        self.assertEqual(loan.fixed_amount, 0.0)

    def test_loan_post_without_computed_lines(self):
        loan = self.create_loan("fixed-annuity", 10000, 1, 12, compute_lines=False)
        self.assertFalse(loan.line_ids)
        loan.post()
        self.assertTrue(loan.line_ids)
        self.assertEqual(loan.state, "posted")

    def test_loan_compute_posted_no_long_term(self):
        """Test _compute_posted_lines"""
        loan = self.create_loan("fixed-annuity", 10000, 1, 12)
        loan.long_term_loan_account_id = False
        self.post(loan)

        with patch(
            "odoo.addons.account_loan.models.account_loan"
            ".AccountLoan._check_long_term_principal_amount"
        ) as patch_long_term_comput:
            loan.compute_lines()
            patch_long_term_comput.assert_not_called()

    def test_loan_line_compute_rate(self):
        loan = self.create_loan("fixed-annuity", 10000, 1, 12)
        previous_interests_amount = loan.interests_amount
        loan.line_ids[0].rate = 2.0
        self.assertNotEqual(
            loan.line_ids[0].interests_amount, previous_interests_amount
        )

    def test_check_amount_on_posted_load_raise(self):
        loan = self.create_loan("fixed-annuity", 10000, 1, 12)
        self.post(loan)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line.view_process_values()
        with self.assertRaisesRegex(
            UserError, "mount cannot be recomputed if moves or invoices exists already"
        ):
            line._check_amount()

    def test_creating_acctount_entries_idempotency(self):
        loan = self.create_loan("fixed-annuity", 10000, 1, 12)
        self.post(loan)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line.view_process_values()
        move_ids_count = len(line.move_ids)
        # Test idempotency to improve coverage
        line.view_process_values()
        self.assertEqual(move_ids_count, len(line.move_ids))

    def test_change_currency(self):
        loan = self.create_loan("fixed-annuity", 500000, 1, 60)
        eur_currency = self.env.ref("base.EUR")
        usd_currency = self.env.ref("base.USD")
        eur_currency.active = True
        loan.journal_id.currency_id = eur_currency
        loan.currency_id = eur_currency
        loan.company_id.currency_id = usd_currency
        self.assertEqual(loan.currency_id, loan.journal_id.currency_id)
        loan.compute_lines()
        for line in loan.line_ids:
            self.assertEqual(line.currency_id, loan.currency_id)

        line = loan.line_ids[0]
        line.view_process_values()

        move_lines = line.mapped("move_ids.line_ids")
        # Credit/Debit lines should be in USD, while amount_currency is in EUR
        self.assertAlmostEqual(
            move_lines[0].credit, -move_lines[0].amount_currency / eur_currency.rate, 2
        )
        self.assertAlmostEqual(
            move_lines[1].debit, move_lines[1].amount_currency / eur_currency.rate, 2
        )
        self.assertAlmostEqual(
            move_lines[2].debit, move_lines[2].amount_currency / eur_currency.rate, 2
        )

    def test_post_with_residual_amount(self):
        loan = self.create_loan("fixed-annuity", 30000, 1, 36, compute_lines=False)
        loan.residual_amount = 600
        loan.compute_lines()
        self.post(loan)
        self.assertEqual(loan.state, "posted")

    @freeze_time("2025-01-01")
    def test_force_posted(self):
        self.env["ir.config_parameter"].set_param(
            "account_loan.auto_post_loan_moves_at_date", "false"
        )
        loan = self.create_loan("fixed-annuity", 30000, 1, 36, compute_lines=False)
        loan.start_date = "2025-02-01"
        self.assertFalse(loan.move_ids)
        post = (
            self.env["account.loan.post"]
            .with_context(default_loan_id=loan.id)
            .create({})
        )
        post.run()
        self.assertTrue(loan.move_ids)
        for move in loan.move_ids:
            self.assertEqual(move.state, "posted")

    @freeze_time("2025-01-01")
    def test_auto_poste(self):
        self.env["ir.config_parameter"].set_param(
            "account_loan.auto_post_loan_moves_at_date", "true"
        )
        loan = self.create_loan("fixed-annuity", 30000, 1, 36, compute_lines=False)
        loan.start_date = "2025-02-01"
        self.assertFalse(loan.move_ids)
        post = (
            self.env["account.loan.post"]
            .with_context(default_loan_id=loan.id)
            .create({})
        )
        post.run()
        self.assertTrue(loan.move_ids)
        for move in loan.move_ids:
            self.assertEqual(move.state, "draft")
            self.assertEqual(move.auto_post, "at_date")

    def test_loan_post_partner_id(self):
        """Test that account_loan_post sets partner_id from loan"""
        contact = self.env["res.partner"].create(
            {"name": "Test contact", "parent_id": self.partner.id}
        )
        loan = self.create_loan(
            "fixed-annuity", 30000, 1, 36, compute_lines=False, partner=contact
        )
        self.post(loan)
        line = loan.line_ids.filtered(lambda r: r.sequence == 1)
        line.view_process_values()
        self.assertEqual(len(loan.move_ids), 2)
        self.assertTrue(loan.move_ids.line_ids)
        for move in loan.move_ids:
            self.assertEqual(move.partner_id, contact)
            for line in move.line_ids:
                self.assertEqual(line.partner_id, self.partner)
