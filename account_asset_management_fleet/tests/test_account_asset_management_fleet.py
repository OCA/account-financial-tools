# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tests import SavepointCase


class TestAccountAsset(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.vehicle = cls.env.ref("fleet.vehicle_1")
        cls.vehicle_2 = cls.env.ref("fleet.vehicle_5")
        cls.partner = cls.env.ref("base.res_partner_2")
        cls.default_account_assets = cls.env["account.account"].search(
            [
                ("company_id", "=", cls.company.id),
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_current_assets").id,
                ),
            ],
            limit=1,
        )
        cls.default_account_expense = cls.env["account.account"].search(
            [
                ("company_id", "=", cls.company.id),
                (
                    "user_type_id",
                    "=",
                    cls.env.ref("account.data_account_type_expenses").id,
                ),
            ],
            limit=1,
        )
        cls.default_journal_purchase = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "purchase")], limit=1
        )
        cls.asset_profile = cls.env["account.asset.profile"].create(
            {
                "company_id": cls.env.company.id,
                "account_expense_depreciation_id": cls.default_account_expense.id,
                "account_asset_id": cls.default_account_assets.id,
                "account_depreciation_id": cls.default_account_assets.id,
                "journal_id": cls.default_journal_purchase.id,
                "name": "Test Profile",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
            }
        )
        cls.asset = cls.env["account.asset"].create(
            {
                "name": "Test Asset",
                "vehicle_id": cls.vehicle.id,
                "profile_id": cls.asset_profile.id,
                "date_start": "2000-01-01",
                "method_time": "year",
                "method_number": 3,
                "method_period": "month",
                "purchase_value": 10000.0,
            }
        )
        cls.move_line_debit_vals = {
            "account_id": cls.default_account_assets.id,
            "debit": 10000.0,
            "credit": 0.0,
            "vehicle_id": cls.vehicle.id,
            "asset_profile_id": cls.asset_profile.id,
            "name": "Vehicle purchase",
        }
        cls.move_line_credit_vals = {
            "account_id": cls.default_account_expense.id,
            "debit": 0.0,
            "credit": 10000.0,
            "vehicle_id": cls.vehicle.id,
            "name": "Payment for vehicle",
        }
        cls.move = cls.env["account.move"].create(
            {
                "partner_id": cls.partner.id,
                "line_ids": [
                    (0, 0, cls.move_line_debit_vals),
                    (0, 0, cls.move_line_credit_vals),
                ],
            }
        )

    def test_inverse_vehicle(self):
        self.assertEqual(self.asset.vehicle_id.id, self.vehicle.id)
        self.assertEqual(self.vehicle.asset_id.id, self.asset.id)

    def test_action_open_vehicle(self):
        action = self.asset.action_open_vehicle()
        self.assertEqual(action["res_model"], "fleet.vehicle")
        self.assertEqual(action["res_id"], self.vehicle.id)
        self.assertEqual(action["view_mode"], "form")

    def test_prepare_asset_vals_vehicle_existing_asset(self):
        aml = self.move.line_ids.filtered(lambda x: x.debit > 0)
        with self.assertRaises(UserError):
            self.env["account.move"]._prepare_asset_vals(aml)

    def test_prepare_asset_vals_vehicle_mismatching_asset(self):
        new_asset = self.env["account.asset"].create(
            {
                "name": "Test Asset 2",
                "vehicle_id": self.vehicle_2.id,
                "profile_id": self.asset_profile.id,
                "date_start": "2000-01-01",
                "method_time": "year",
                "method_number": 3,
                "method_period": "month",
                "purchase_value": 12000.0,
            }
        )
        self.move_line_debit_vals["asset_id"] = new_asset.id

        ctx = dict(self.env.context, allow_asset=True, check_move_validity=False)
        new_move = (
            self.env["account.move"]
            .with_context(ctx)
            .create(
                {
                    "partner_id": self.partner.id,
                    "line_ids": [
                        (0, 0, self.move_line_debit_vals),
                        (0, 0, self.move_line_credit_vals),
                    ],
                }
            )
        )
        aml = new_move.line_ids.filtered(lambda x: x.debit > 0)

        with self.assertRaises(UserError):
            self.env["account.move"]._prepare_asset_vals(aml)

    def test_prepare_asset_vals_valid(self):
        self.move_line_debit_vals["asset_id"] = self.asset.id

        ctx = dict(self.env.context, allow_asset=True, check_move_validity=False)
        new_move = (
            self.env["account.move"]
            .with_context(ctx)
            .create(
                {
                    "partner_id": self.partner.id,
                    "line_ids": [
                        (0, 0, self.move_line_debit_vals),
                        (0, 0, self.move_line_credit_vals),
                    ],
                }
            )
        )
        aml = new_move.line_ids.filtered(lambda x: x.debit > 0)

        result = self.env["account.move"]._prepare_asset_vals(aml)
        self.assertEqual(result["vehicle_id"], self.vehicle)

    def test_compute_asset_values(self):
        self.vehicle._compute_asset_values()
        self.assertEqual(self.vehicle.net_car_value, 10000.0)
        self.assertEqual(self.vehicle.residual_value, 10000.0)

        self.asset.write({"purchase_value": 12000.0})
        self.vehicle._compute_asset_values()
        self.assertEqual(self.vehicle.net_car_value, 12000.0)
        self.assertEqual(self.vehicle.residual_value, 12000.0)
