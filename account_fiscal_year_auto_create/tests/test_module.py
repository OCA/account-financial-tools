# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date, datetime

from odoo.addons.base.tests.common import BaseCommon


class TestFiscalYear(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.AccountFiscalYear = cls.env["account.fiscal.year"]
        cls.company = cls.env["res.company"].create(
            {
                "name": "Demo Company (account_fiscal_year_auto_create)",
            }
        )

        cls.last_year = datetime.now().year - 1
        cls.last_fiscal_year = cls.AccountFiscalYear.create(
            {
                "name": f"FY {cls.last_year}",
                "date_from": date(cls.last_year, 1, 1),
                "date_to": date(cls.last_year, 12, 31),
                "company_id": cls.company.id,
            }
        )

    def test_cron_auto_create(self):
        """It should create new fiscal year via cron and not duplicate"""
        # Step 1: Run cron -> should create one new fiscal year
        old_fiscal_year_ids = self.AccountFiscalYear.search([]).ids
        self.AccountFiscalYear.cron_auto_create()

        new_fy = self.AccountFiscalYear.search([("id", "not in", old_fiscal_year_ids)])
        self.assertEqual(len(new_fy), 1, "A new fiscal year should be created.")

        expected_year = self.last_year + 1
        self.assertEqual(new_fy.name, f"FY {expected_year}")
        self.assertEqual(new_fy.date_from, date(expected_year, 1, 1))
        self.assertEqual(new_fy.date_to, date(expected_year, 12, 31))

        # Step 2: Run cron again -> should NOT create duplicate fiscal year
        new_ids = self.AccountFiscalYear.search([]).ids
        self.AccountFiscalYear.cron_auto_create()
        newer_fy = self.AccountFiscalYear.search([("id", "not in", new_ids)])
        self.assertFalse(newer_fy, "No new fiscal year should be created again.")
