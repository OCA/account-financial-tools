# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from decimal import ROUND_HALF_UP, Decimal

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

CENT = Decimal("0.01")


@tagged("post_install", "-at_install")
class TestDepreciationRounding(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.profile = cls.env["account.asset.profile"].create(
            {
                "name": "Rounding profile",
                "account_expense_depreciation_id": cls.company_data[
                    "default_account_expense"
                ].id,
                "account_asset_id": cls.company_data["default_account_assets"].id,
                "account_depreciation_id": cls.company_data[
                    "default_account_assets"
                ].id,
                "journal_id": cls.company_data["default_journal_purchase"].id,
                "method_time": "year",
                "method_number": 5,
                "method_period": "year",
            }
        )

    def _board(self, value, method, years, factor=0.0):
        asset = self.env["account.asset"].create(
            {
                "name": "rounding asset",
                "profile_id": self.profile.id,
                "purchase_value": value,
                "salvage_value": 0,
                "date_start": "2026-01-01",
                "method_time": "year",
                "method": method,
                "method_progress_factor": factor,
                "method_number": years,
                "method_period": "year",
                "prorata": False,
            }
        )
        asset.compute_depreciation_board()
        asset.invalidate_recordset()
        lines = asset.depreciation_line_ids.filtered(
            lambda line: line.type == "depreciate"
        ).sorted("line_date")
        return asset, lines

    def _cent_degressive(self, value, factor, years):
        """Schedule computed in exact cents: each year rounds residual * factor
        half-up, the last year takes what is left."""
        residual = Decimal(str(value))
        rate = Decimal(str(factor))
        amounts = []
        for year in range(1, years + 1):
            if year == years:
                amount = residual
            else:
                amount = (residual * rate).quantize(CENT, rounding=ROUND_HALF_UP)
            amounts.append(amount)
            residual -= amount
        return amounts

    def _assert_board(self, lines, expected):
        self.assertEqual(len(lines), len(expected))
        got = [Decimal(str(line.amount)).quantize(CENT) for line in lines]
        diffs = [
            (i + 1, str(e), str(g))
            for i, (e, g) in enumerate(zip(expected, got, strict=True))
            if e != g
        ]
        self.assertEqual(diffs, [], "(year, expected, got)")

    def _line_of(self, lines, date):
        return lines.filtered(lambda line: line.line_date == fields.Date.to_date(date))

    def test_degressive_long_schedule_keeps_cents(self):
        _asset, lines = self._board(10000.00, "degressive", 96, 0.05)
        self.assertEqual(self._line_of(lines, "2107-12-31").amount, 7.85)
        self._assert_board(lines, self._cent_degressive(10000.00, 0.05, 96))
        self.assertAlmostEqual(sum(lines.mapped("amount")), 10000.00, places=2)

    def test_degressive_long_schedule_factor_10(self):
        _asset, lines = self._board(10000.00, "degressive", 47, 0.10)
        self.assertEqual(self._line_of(lines, "2063-12-31").amount, 20.28)
        self._assert_board(lines, self._cent_degressive(10000.00, 0.10, 47))

    def test_degressive_long_schedule_negative_value(self):
        _asset, lines = self._board(-10000.00, "degressive", 96, 0.05)
        self.assertEqual(self._line_of(lines, "2107-12-31").amount, -7.85)
        self._assert_board(lines, self._cent_degressive(-10000.00, 0.05, 96))

    def test_degressive_short_schedule_unchanged(self):
        _asset, lines = self._board(1000.00, "degressive", 5, 0.40)
        self._assert_board(
            lines,
            [Decimal(a) for a in ("400.00", "240.00", "144.00", "86.40", "129.60")],
        )

    def test_linear_schedule_unchanged(self):
        _asset, lines = self._board(1000.00, "linear", 3)
        self._assert_board(lines, [Decimal(a) for a in ("333.33", "333.33", "333.34")])
