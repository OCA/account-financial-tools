# Copyright 2026 Acsone
# Author: Pierre Verkest <pierre.verkest@apycod.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("-at_install", "post_install")
class TestAccountSingleCompany(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.company_data["company"]
        cls.company_data_2 = cls.setup_other_company(name="Company 2")
        cls.company_b = cls.company_data_2["company"]

        cls.env.user.write({"company_ids": [(4, cls.company_b.id)]})

        cls.single_company_account = cls.env["account.account"].create(
            {
                "name": "Single Company Account",
                "code": "123456",
                "account_type": "asset_current",
                "company_ids": [(6, 0, [cls.company_a.id])],
            }
        )

        cls.multi_company_account = cls.env["account.account"].create(
            {
                "name": "Multi Company Account",
                "account_type": "asset_current",
                "company_ids": [(6, 0, [cls.company_a.id, cls.company_b.id])],
                "code_mapping_ids": [
                    (0, 0, {"company_id": cls.company_a.id, "code": "654321"}),
                    (0, 0, {"company_id": cls.company_b.id, "code": "654322"}),
                ],
            }
        )

    def test_single_company_account_code_and_display_name_in_own_company_context(
        self,
    ):
        account = self.single_company_account.with_company(self.company_a)
        self.assertEqual(account.code, "123456")
        self.assertIn("123456", account.display_name)

    def test_single_company_account_code_and_display_name_in_other_company_context(
        self,
    ):
        account = self.single_company_account.with_company(self.company_b)
        self.assertEqual(account.code, "123456")
        self.assertIn("123456", account.display_name)

    def test_search_single_company_account_by_code_from_other_company_context(
        self,
    ):
        accounts = (
            self.env["account.account"]
            .sudo()
            .with_company(self.company_b)
            .search([("code", "=", "123456")])
        )
        self.assertIn(self.single_company_account, accounts)

    def test_search_single_company_account_by_display_name_from_other_company_context(
        self,
    ):
        accounts = (
            self.env["account.account"]
            .sudo()
            .with_company(self.company_b)
            .search([("display_name", "ilike", "123456")])
        )
        self.assertIn(self.single_company_account, accounts)

    def test_multi_company_account_code_store_single_company_is_false(self):
        self.assertFalse(self.multi_company_account.code_store_single_company)

    def test_field_to_sql_for_code_includes_single_company_code(self):
        query = (
            self.env["account.account"]
            .sudo()
            .with_company(self.company_b)
            ._search([("code", "=", "123456")])
        )
        accounts = self.env["account.account"].sudo().browse(query)
        self.assertIn(self.single_company_account, accounts)
