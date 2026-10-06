# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo.tests.common import TransactionCase


class TestAccountEbitdaReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure that models are loaded
        cls.report_bottom_up = cls.env.ref(
            "account_ebitda_report.mis_report_ebitda_bottom_up",
            raise_if_not_found=False,
        )
        cls.report_top_down = cls.env.ref(
            "account_ebitda_report.mis_report_ebitda_top_down", raise_if_not_found=False
        )
        cls.report_pro = cls.env.ref(
            "account_ebitda_report.mis_report_ebitda_pro", raise_if_not_found=False
        )

    def test_01_reports_loaded(self):
        """Test if the MIS reports are correctly loaded into the database."""
        self.assertTrue(self.report_bottom_up, "Bottom-up EBITDA report not loaded.")
        self.assertTrue(self.report_top_down, "Top-down EBITDA report not loaded.")
        self.assertTrue(self.report_pro, "Professional EBITDA report not loaded.")

    def test_02_kpi_expressions(self):
        """Test if the KPIs exist and have expressions defined."""
        if self.report_pro:
            kpi_revenue = self.env.ref("account_ebitda_report.mis_kpi_pro_revenue")
            self.assertTrue(kpi_revenue)
            self.assertTrue(kpi_revenue.expression)

            kpi_ebitda = self.env.ref("account_ebitda_report.mis_kpi_pro_ebitda")
            self.assertTrue(kpi_ebitda)
            self.assertIn("REV", kpi_ebitda.expression)

    def test_03_account_tags(self):
        """Test if the required account tags are created."""
        tag = self.env.ref(
            "account_ebitda_report.account_tag_ebitda_taxes", raise_if_not_found=False
        )
        self.assertTrue(tag, "EBITDA / Taxes tag not loaded.")

        tag_ma = self.env.ref(
            "account_ebitda_report.account_tag_ebitda_ma_salary",
            raise_if_not_found=False,
        )
        self.assertTrue(tag_ma, "EBITDA / M&A Owner Salary tag not loaded.")
