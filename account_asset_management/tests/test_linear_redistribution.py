# Copyright 2026 FactorLibre - Aritz Olea <aritz.olea@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api, registry
from odoo.tests import get_db_name, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestLinearRedistribution(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        with registry(get_db_name()).cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            if not env.ref("l10n_generic_coa.configurable_chart_template", False):
                coa = env["account.chart.template"].search([("visible", "=", True)])[:1]
                chart_template_ref = coa.get_external_id()[coa.id]
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.asset_model = cls.env["account.asset"]
        cls.asset_profile_model = cls.env["account.asset.profile"]
        cls.dl_model = cls.env["account.asset.line"]
        cls.profile = cls.asset_profile_model.create(
            {
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "name": "Linear 17 Years",
                "method_time": "year",
                "method_number": 17,
                "method_period": "year",
            }
        )

    def _create_asset(self, vals=None):
        defaults = {
            "name": "Test Asset",
            "profile_id": self.profile.id,
            "purchase_value": 2407.56,
            "salvage_value": 0,
            "date_start": "2008-01-01",
            "method_time": "year",
            "method_number": 17,
            "method_period": "year",
            "method": "linear",
        }
        if vals:
            defaults.update(vals)
        return self.asset_model.create(defaults)

    def _mark_lines_as_init(self, asset, count):
        lines = asset.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate"
        ).sorted("line_date")
        for line in lines[:count]:
            line.init_entry = True

    def test_01_redistribution_basic(self):
        """7 init_entry lines, then recompute. The 10 remaining unposted
        lines should have uniform amounts = residual / 10."""
        asset = self._create_asset()
        asset.compute_depreciation_board()
        self._mark_lines_as_init(asset, 7)
        asset.compute_depreciation_board()
        currency = asset.company_id.currency_id
        posted_lines = asset.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate" and (l.move_check or l.init_entry)
        )
        unposted_lines = asset.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate" and not l.move_check and not l.init_entry
        ).sorted("line_date")
        self.assertEqual(len(posted_lines), 7)
        self.assertEqual(len(unposted_lines), 10)
        posted_total = sum(posted_lines.mapped("amount"))
        residual = currency.round(asset.depreciation_base - posted_total)
        expected_uniform = currency.round(residual / 10)
        for line in unposted_lines[:-1]:
            self.assertEqual(
                line.amount,
                expected_uniform,
                f"Line {line.line_date}: expected {expected_uniform}, "
                f"got {line.amount}",
            )
        total = sum(
            asset.depreciation_line_ids.filtered(
                lambda l: l.type == "depreciate"
            ).mapped("amount")
        )
        self.assertTrue(
            currency.is_zero(currency.round(total - asset.depreciation_base)),
            f"Sum integrity failed: {total} != {asset.depreciation_base}",
        )

    def test_02_no_redistribution_no_posted(self):
        """Asset with no posted lines should not trigger redistribution."""
        asset = self._create_asset()
        asset.compute_depreciation_board()
        depr_lines = asset.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate"
        )
        amounts = depr_lines.mapped("amount")
        currency = asset.company_id.currency_id
        expected = currency.round(asset.depreciation_base / 17)
        for amt in amounts[:-1]:
            self.assertEqual(amt, expected)

    def test_03_no_redistribution_degressive(self):
        """Degressive method should not trigger redistribution."""
        asset = self._create_asset(
            {
                "method": "degressive",
                "method_progress_factor": 0.3,
            }
        )
        asset.compute_depreciation_board()
        self._mark_lines_as_init(asset, 3)
        asset.compute_depreciation_board()
        self.assertFalse(asset._should_redistribute_linear())

    def test_04_sum_integrity(self):
        """Sum of all depreciation lines equals depreciation_base
        after redistribution with various posted line counts."""
        for n_posted in (1, 5, 10, 14):
            asset = self._create_asset()
            asset.compute_depreciation_board()
            self._mark_lines_as_init(asset, n_posted)
            asset.compute_depreciation_board()
            currency = asset.company_id.currency_id
            total = sum(
                asset.depreciation_line_ids.filtered(
                    lambda l: l.type == "depreciate"
                ).mapped("amount")
            )
            self.assertTrue(
                currency.is_zero(currency.round(total - asset.depreciation_base)),
                f"Sum integrity failed with {n_posted} posted lines: "
                f"{total} != {asset.depreciation_base}",
            )

    def test_05_two_unposted_skipped(self):
        """With only 2 unposted lines, redistribution should not activate."""
        asset = self._create_asset()
        asset.compute_depreciation_board()
        self._mark_lines_as_init(asset, 15)
        asset.compute_depreciation_board()
        unposted_lines = asset.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate" and not l.move_check and not l.init_entry
        )
        self.assertEqual(len(unposted_lines), 2)
        currency = asset.company_id.currency_id
        total = sum(
            asset.depreciation_line_ids.filtered(
                lambda l: l.type == "depreciate"
            ).mapped("amount")
        )
        self.assertTrue(
            currency.is_zero(currency.round(total - asset.depreciation_base)),
        )

    def test_06_no_redistribution_prorata(self):
        """Prorata assets should not trigger redistribution."""
        asset = self._create_asset(
            {
                "prorata": True,
                "date_start": "2008-07-07",
            }
        )
        asset.compute_depreciation_board()
        self._mark_lines_as_init(asset, 3)
        asset.compute_depreciation_board()
        self.assertFalse(asset._should_redistribute_linear())
