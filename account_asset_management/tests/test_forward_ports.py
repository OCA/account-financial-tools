# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAssetForwardPorts(AccountTestInvoicingCommon):
    """Tests for the fixes forward-ported from 18.0 (OCA PR #2426)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_model = cls.env["account.asset"]
        cls.asset_profile_model = cls.env["account.asset.profile"]
        profile_vals = {
            "account_expense_depreciation_id": cls.company_data[
                "default_account_expense"
            ].id,
            "account_asset_id": cls.company_data["default_account_assets"].id,
            "account_depreciation_id": cls.company_data["default_account_assets"].id,
            "journal_id": cls.company_data["default_journal_purchase"].id,
            "method_time": "year",
            "method_period": "year",
        }
        cls.ict3Y = cls.asset_profile_model.create(
            dict(profile_vals, name="Hardware - 3 Years", method_number=3)
        )
        cls.car5y = cls.asset_profile_model.create(
            dict(profile_vals, name="Cars - 5 Years", method_number=5)
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "invoice_date": fields.Date.context_today(cls.env.user),
                "partner_id": cls.partner.id,
                "invoice_line_ids": [
                    Command.create(
                        {"name": "test", "price_unit": 2000.00, "quantity": 1}
                    ),
                ],
            }
        )

    def _new_asset(self, **vals):
        return self.asset_model.create(
            {
                "name": "test asset",
                "profile_id": self.car5y.id,
                "purchase_value": 1000,
                "date_start": "2020-01-01",
                **vals,
            }
        )

    def test_bi_report_values(self):
        asset = self._new_asset()
        asset.compute_depreciation_board()
        asset.validate()
        lines = asset.depreciation_line_ids.filtered(
            lambda x: x.type == "depreciate"
        ).sorted("line_date")
        self.assertEqual(len(lines), 5)
        lines[0].create_move()
        self.env.flush_all()
        rows = self.env["account.asset.report"].search([("asset_id", "=", asset.id)])
        self.assertEqual(sum(rows.mapped("depreciation_count")), 5)
        self.assertAlmostEqual(sum(rows.mapped("gross_value")), 1000)
        self.assertAlmostEqual(sum(rows.mapped("posted_value")), lines[0].amount)
        self.assertAlmostEqual(
            sum(rows.mapped("unposted_value")), 1000 - lines[0].amount
        )
        self.assertEqual(rows.asset_profile_id, self.car5y)

    def test_account_asset_profile_company_dependent(self):
        company_b = self.setup_other_company(name="Company B")["company"]
        account = self.company_data["default_account_assets"]
        account.company_ids |= company_b
        profile_b = self.asset_profile_model.with_company(company_b).create(
            {
                "account_expense_depreciation_id": account.id,
                "account_asset_id": account.id,
                "account_depreciation_id": account.id,
                "journal_id": self.env["account.journal"]
                .search(
                    [("company_id", "=", company_b.id), ("type", "=", "purchase")],
                    limit=1,
                )
                .id,
                "company_id": company_b.id,
                "name": "Company B profile",
                "method_time": "year",
                "method_number": 3,
                "method_period": "year",
            }
        )
        account.with_company(self.env.company).asset_profile_id = self.ict3Y
        account.with_company(company_b).asset_profile_id = profile_b
        self.assertEqual(
            account.with_company(self.env.company).asset_profile_id, self.ict3Y
        )
        self.assertEqual(account.with_company(company_b).asset_profile_id, profile_b)

    def test_compute_button_only_in_draft(self):
        arch = self.asset_model.get_view(view_type="form")["arch"]
        button = etree.fromstring(arch).xpath(
            "//button[@name='compute_depreciation_board']"
        )
        self.assertEqual(len(button), 1)
        self.assertEqual(button[0].get("invisible"), "state != 'draft'")

    def test_first_line_created_with_imported_depreciation_line(self):
        asset = self._new_asset(
            depreciation_line_ids=[
                Command.create(
                    {
                        "name": "imported",
                        "type": "depreciate",
                        "amount": 200,
                        "line_date": "2020-12-31",
                        "init_entry": True,
                    }
                )
            ]
        )
        create_line = asset.depreciation_line_ids.filtered(lambda x: x.type == "create")
        self.assertEqual(len(create_line), 1)
        self.assertAlmostEqual(create_line.amount, 1000)
