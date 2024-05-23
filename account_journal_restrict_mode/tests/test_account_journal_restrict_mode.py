# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountJournalRestrictMode(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.account_journal_obj = cls.env["account.journal"]
        cls.company_obj = cls.env["res.company"]
        cls.currency_obj = cls.env["res.currency"]
        cls.chart_template_obj = cls.env["account.chart.template"]
        cls.country_be = cls.env.ref("base.be")  # Refs

    def test_journal_default_lock_entries(self):
        journal = self.account_journal_obj.create(
            {"name": "Test Journal", "code": "TJ", "type": "general"}
        )
        self.assertTrue(journal.restrict_mode_hash_table)
        with self.assertRaises(UserError):
            journal.write({"restrict_mode_hash_table": False})

    def test_journal_default_secure_sequence_new_company(self):
        test_company = self.company_obj.create(
            {
                "name": "My Test Company",
                "currency_id": self.currency_obj.search([("name", "=", "USD")]).id,
                "country_id": self.country_be.id,
            }
        )
        self.chart_template_obj.try_loading(
            template_code="generic_coa", company=test_company, install_demo=False
        )
        journals = self.env["account.journal"].search(
            [("company_id", "=", test_company.id)]
        )
        self.assertTrue(journals)
        self.assertTrue(
            all(
                journal.restrict_mode_hash_table and journal.secure_sequence_id
                for journal in journals
            )
        )
