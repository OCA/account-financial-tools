# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from odoo.tests.common import TransactionCase


class TestModule(TransactionCase):
    def setUp(self):
        super().setUp()
        self.AccountFiscalYear = self.env["account.fiscal.year"]
        self.company = self.env["res.company"].create(
            {
                "name": "Demo Company (account_fiscal_year_auto_create)",
            }
        )

        # create a fiscal year
        self.last_year = datetime.now().year - 1
        self.last_fiscal_year = self.AccountFiscalYear.create(
            {
                "name": "FY %d" % (self.last_year),
                "date_from": date(self.last_year, 1, 1).strftime("%Y-%m-%d"),
                "date_to": date(self.last_year, 12, 31).strftime("%Y-%m-%d"),
                "company_id": self.company.id,
            }
        )

    def test_cron(self):
        # Run cron should create a new fiscal year
        existing_fiscal_years = self.AccountFiscalYear.search([])
        self.AccountFiscalYear.cron_auto_create()

        new_fiscal_year = self.AccountFiscalYear.search(
            [("id", "not in", existing_fiscal_years.ids)]
        )
        self.assertTrue(new_fiscal_year)
        self.assertEqual(new_fiscal_year.name, "FY %d" % (self.last_year + 1))
        self.assertEqual(new_fiscal_year.date_from, date(self.last_year + 1, 1, 1))
        self.assertEqual(new_fiscal_year.date_from, date(self.last_year + 1, 1, 1))
        self.assertEqual(new_fiscal_year.name, "FY %d" % (self.last_year + 1))

        # Rerun cron should not create a new fiscal year
        existing_fiscal_years = self.AccountFiscalYear.search([])
        self.AccountFiscalYear.cron_auto_create()

        new_fiscal_year = self.AccountFiscalYear.search(
            [("id", "not in", existing_fiscal_years.ids)]
        )
        self.assertFalse(new_fiscal_year)
