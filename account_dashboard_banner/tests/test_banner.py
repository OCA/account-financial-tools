# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountDashboardBanner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cell_obj = cls.env["account.dashboard.banner.cell"]
        cls.test_custom_label = "TEST Custom Label"
        cls.test_custom_tooltip = "TEST customer tooltip"
        # add cell_types that don't already exists
        existing = cls.cell_obj.search_read([], ["cell_type"])
        existing_cell_types = [x["cell_type"] for x in existing]
        to_create_vals = []
        for cell_type in [
            "income_fiscalyear",
            "income_year",
            "income_quarter",
            "income_month",
            "liquidity",
            "customer_debt",
            "customer_overdue",
            "supplier_debt",
            "tax_lock_date",
            "sale_lock_date",
            "purchase_lock_date",
            "fiscalyear_lock_date",
            "hard_lock_date",
        ]:
            if cell_type not in existing_cell_types:
                to_create_vals.append({"cell_type": cell_type})
        cls.cell_obj.create(to_create_vals)
        fy_lock_cell = cls.cell_obj.search([("cell_type", "=", "fiscalyear_lock_date")])
        fy_lock_cell.write(
            {
                "custom_label": cls.test_custom_label,
                "custom_tooltip": cls.test_custom_tooltip,
                "warn": True,
            }
        )

    def test_banner(self):
        res = self.cell_obj.get_banner_data()
        self.assertIsInstance(res, dict)
        self.assertEqual(len(res), self.cell_obj.search_count([]))
        for cell_entry in res.items():
            cell_data = cell_entry[1]
            if cell_data["cell_type"] == "fiscalyear_lock_date":
                self.assertEqual(cell_data["label"], self.test_custom_label)
                self.assertEqual(cell_data["tooltip"], self.test_custom_tooltip)
                if not self.env.company.fiscalyear_lock_date:
                    self.assertTrue(cell_data.get("warn"))
