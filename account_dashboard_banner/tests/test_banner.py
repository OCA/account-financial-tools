# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.account_dashboard_banner.post_install import (
    create_default_account_dashboard_cells,
)


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

    def test_post_install_hook(self):
        create_default_account_dashboard_cells(self.env)

    def test_display_name(self):
        cell = self.cell_obj.search([("cell_type", "=", "liquidity")], limit=1)
        self.assertTrue(cell.display_name)
        cell.custom_label = "Custom Liquidity"
        self.assertEqual(cell.display_name, "Custom Liquidity")

    def test_warn_config_validation_error(self):
        with self.assertRaises(ValidationError):
            self.cell_obj.create(
                {
                    "cell_type": "liquidity",
                    "warn": True,
                    "warn_type": "outside",
                    "warn_min": 100.0,
                    "warn_max": 50.0,
                }
            )

    def test_warn_thresholds(self):
        cell_under = self.cell_obj.create(
            {
                "cell_type": "liquidity",
                "warn": True,
                "warn_type": "under",
                "warn_min": 1000.0,
            }
        )
        self.assertTrue(cell_under.warn_type_show)
        cell_data_under = {"raw_value": 500.0}
        cell_under._update_cell_warn(cell_data_under)
        self.assertTrue(cell_data_under.get("warn"))

        cell_above = self.cell_obj.create(
            {
                "cell_type": "customer_debt",
                "warn": True,
                "warn_type": "above",
                "warn_max": 100.0,
            }
        )
        cell_data_above = {"raw_value": 200.0}
        cell_above._update_cell_warn(cell_data_above)
        self.assertTrue(cell_data_above.get("warn"))

        cell_outside = self.cell_obj.create(
            {
                "cell_type": "customer_debt",
                "warn": True,
                "warn_type": "outside",
                "warn_min": 10.0,
                "warn_max": 100.0,
            }
        )
        cell_data_outside = {"raw_value": 150.0}
        cell_outside._update_cell_warn(cell_data_outside)
        self.assertTrue(cell_data_outside.get("warn"))

        cell_inside = self.cell_obj.create(
            {
                "cell_type": "customer_debt",
                "warn": True,
                "warn_type": "inside",
                "warn_min": 10.0,
                "warn_max": 100.0,
            }
        )
        cell_data_inside = {"raw_value": 50.0}
        cell_inside._update_cell_warn(cell_data_inside)
        self.assertTrue(cell_data_inside.get("warn"))

    def test_old_lock_date_warning(self):
        old_date = fields.Date.today() - relativedelta(days=100)
        self.env.company.fiscalyear_lock_date = old_date
        fy_lock_cell = self.cell_obj.search(
            [("cell_type", "=", "fiscalyear_lock_date")], limit=1
        )
        fy_lock_cell.write({"warn": True, "warn_lock_date_days": 30})
        speedy = fy_lock_cell._prepare_speedy(self.env.company)
        cell_data = fy_lock_cell._prepare_cell_data(self.env.company, speedy)
        self.assertTrue(cell_data.get("warn"))
