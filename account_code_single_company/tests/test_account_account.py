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

    def test_search_multi_company_account_by_placeholder_code_in_own_company_context(
        self,
    ):
        accounts = (
            self.env["account.account"]
            .sudo()
            .with_company(self.company_a)
            .search([("placeholder_code", "=ilike", "654321")])
        )
        self.assertIn(self.multi_company_account, accounts)

    def test_search_single_company_account_by_placeholder_code_other_company(
        self,
    ):
        # Search single-company account by placeholder_code (=ilike)
        # from other company context.
        accounts = (
            self.env["account.account"]
            .sudo()
            .with_company(self.company_b)
            .search([("placeholder_code", "=ilike", "123456")])
        )
        self.assertIn(self.single_company_account, accounts)

    def test_search_single_company_account_by_placeholder_code_in_operator(
        self,
    ):
        # Search single-company account by placeholder_code using 'in'
        # operator from other company context.
        accounts = (
            self.env["account.account"]
            .sudo()
            .with_company(self.company_b)
            .search([("placeholder_code", "in", ["123456"])])
        )
        self.assertIn(self.single_company_account, accounts)

    def test_search_placeholder_code_with_unsupported_operator_returns_not_implemented(
        self,
    ):
        res = self.env["account.account"]._search_placeholder_code("like", "123456")
        self.assertIs(res, NotImplemented)

    def test_field_to_sql_for_code_multi_company_account(
        self,
    ):
        # _field_to_sql for code on multi-company account returns active
        # company code via COALESCE (fails if COALESCE is missing).
        query = (
            self.env["account.account"]
            .sudo()
            .with_company(self.company_a)
            ._search([("id", "=", self.multi_company_account.id)])
        )
        code_sql = (
            self.env["account.account"]
            .with_company(self.company_a)
            ._field_to_sql("account_account", "code", query)
        )
        res = self.env.execute_query(query.select(code_sql))
        self.assertEqual(res, [("654321",)])

    def test_field_to_sql_for_placeholder_code_multi_company_account(
        self,
    ):
        # _field_to_sql for placeholder_code on multi-company account
        # returns active company code via COALESCE.
        query = (
            self.env["account.account"]
            .sudo()
            .with_company(self.company_a)
            ._search([("id", "=", self.multi_company_account.id)])
        )
        placeholder_code_sql = (
            self.env["account.account"]
            .with_company(self.company_a)
            ._field_to_sql("account_account", "placeholder_code", query)
        )
        res = self.env.execute_query(query.select(placeholder_code_sql))
        self.assertEqual(res, [("654321",)])

    def test_field_to_sql_for_placeholder_code_single_company_other_company(
        self,
    ):
        # _field_to_sql for placeholder_code on single-company account
        # from other company context returns single-company code via COALESCE.
        query = (
            self.env["account.account"]
            .sudo()
            .with_company(self.company_b)
            ._search([("id", "=", self.single_company_account.id)])
        )
        placeholder_code_sql = (
            self.env["account.account"]
            .with_company(self.company_b)
            ._field_to_sql("account_account", "placeholder_code", query)
        )
        res = self.env.execute_query(query.select(placeholder_code_sql))
        self.assertEqual(res, [("123456",)])

    def test_field_to_sql_for_other_field_falls_back_to_super(self):
        query = (
            self.env["account.account"]
            .sudo()
            .with_company(self.company_a)
            ._search([("id", "=", self.single_company_account.id)])
        )
        name_sql = (
            self.env["account.account"]
            .with_company(self.company_a)
            ._field_to_sql("account_account", "name", query)
        )
        res = self.env.execute_query(query.select(name_sql))
        self.assertEqual(res, [("Single Company Account",)])
