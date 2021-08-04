# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

from datetime import date


class TestModule(TransactionCase):

    def setUp(self):
        super().setUp()
        self.AccountFiscalYear = self.env["account.fiscal.year"]
        self.company = self.env.ref("base.main_company")
        self.account_type_receivable = self.env["account.account.type"].create(
            {"name": "Test Receivable", "type": "receivable"}
        )
        self.account_receivable = self.env["account.account"].create(
            {
                "name": "Test Receivable",
                "code": "TEST_AR",
                "user_type_id": self.account_type_receivable.id,
                "reconcile": True,
            }
        )
        self.sale_journal = self.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", self.company.id)]
        )[0]
        self.sequence = self.sale_journal.sequence_id
        self.sequence.use_date_range = True

        self.account_move = self.env["account.move"].create({
            "journal_id": self.sale_journal.id,
            "company_id": self.company.id,
            "line_ids": [(0, 0, {
                "account_id": self.account_receivable.id,
                "debit": 100,
            }), (0, 0, {
                "account_id": self.account_receivable.id,
                "credit": 100,
            })]
        })

        self.existing_subsequence_ids =\
            self.env["ir.sequence.date_range"].search([
                ("sequence_id", "=", self.sequence.id)]).ids

    def _get_new_subsequence(self):
        return self.env["ir.sequence.date_range"].search([
            ("sequence_id", "=", self.sequence.id),
            ("id", "not in", self.existing_subsequence_ids),
        ])

    def test_method_normal(self):
        """Non Regression Test"""
        self.company.account_subsequence_method = False
        self.account_move.date = "2100-06-01"
        self.account_move.post()
        new_subsequences = self._get_new_subsequence()
        self.assertEqual(len(new_subsequences), 1)
        self.assertEqual(
            new_subsequences[0].date_from,
            date(2100, 1, 1)
        )
        self.assertEqual(
            new_subsequences[0].date_to,
            date(2100, 12, 31)
        )

    def test_method_company_setting_before(self):
        self.company.account_subsequence_method = 'company_setting'
        self.company.fiscalyear_last_day = 31
        self.company.fiscalyear_last_month = 3
        self.account_move.date = "2100-03-15"
        self.account_move.post()

        new_subsequences = self._get_new_subsequence()
        self.assertEqual(len(new_subsequences), 1)
        self.assertEqual(
            new_subsequences[0].date_from,
            date(2099, 4, 1)
        )
        self.assertEqual(
            new_subsequences[0].date_to,
            date(2100, 3, 31)
        )

    def test_method_company_setting_after(self):
        self.company.account_subsequence_method = 'company_setting'
        self.company.fiscalyear_last_day = 31
        self.company.fiscalyear_last_month = 3
        self.account_move.date = "2100-05-15"
        self.account_move.post()

        new_subsequences = self._get_new_subsequence()
        self.assertEqual(len(new_subsequences), 1)
        self.assertEqual(
            new_subsequences[0].date_from,
            date(2100, 4, 1)
        )
        self.assertEqual(
            new_subsequences[0].date_to,
            date(2101, 3, 31)
        )

    def test_method_fiscal_year_setting(self):
        self.company.account_subsequence_method = 'fiscal_year_setting'
        with self.assertRaises(ValidationError):
            self.account_move.date = "2100-06-01"
            self.account_move.post()

        # create a Fiscal Year
        self.AccountFiscalYear.create({
            "name": "2100 FY April to March",
            "company_id": self.company.id,
            "date_from": "2100-04-01",
            "date_to": "2101-03-31",
        })

        # Try to post out the date range
        with self.assertRaises(ValidationError):
            self.account_move.date = "2100-03-31"
            self.account_move.post()

        with self.assertRaises(ValidationError):
            self.account_move.date = "2101-04-01"
            self.account_move.post()

        # Post in the range should succeed
        self.account_move.date = "2100-06-01"
        self.account_move.post()
        new_subsequences = self._get_new_subsequence()
        self.assertEqual(len(new_subsequences), 1)
        self.assertEqual(
            new_subsequences[0].date_from,
            date(2100, 4, 1)
        )
        self.assertEqual(
            new_subsequences[0].date_to,
            date(2101, 3, 31)
        )
