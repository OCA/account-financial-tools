# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestOSSCoA(AccountTestInvoicingCommon):
    # pylint: disable=W8106
    @classmethod
    def setUpClass(cls, chart_template_ref="generic_coa"):
        super().setUpClass()
        cls.chart_template = chart_template_ref
        template = cls.env["account.chart.template"]
        template.try_loading(chart_template_ref, cls.env.company)
        cls.chart_template_data = template._get_chart_template_data(cls.chart_template)
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test account_chart_update company",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.env.user.write(
            {
                "company_ids": [
                    (6, 0, cls.env.user.company_ids.ids),
                    (4, cls.company.id),
                ],
                "company_id": cls.company.id,
                "groups_id": [
                    (6, 0, cls.env.user.groups_id.ids),
                    (4, cls.env.ref("account.group_account_user").id),
                    (4, cls.env.ref("account.group_account_invoice").id),
                    (4, cls.env.ref("base.group_multi_company").id),
                ],
            }
        )
        cls.oss_wizard = cls.env["l10n.eu.oss.wizard"]

    def setUp(self):
        super().setUp()
        # Create demo tax group and tax
        self.tax_group = self.env["account.tax.group"].create({"name": "Test 1"})
        self.tax = self.env["account.tax"].create(
            {
                "name": "Not OSS Demo tax",
                "amount": 10,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "country_id": self.env.ref("base.es").id,
                "company_id": self.company.id,
                "tax_group_id": self.tax_group.id,
            }
        )
        self.wizard_obj = self.env["wizard.update.charts.accounts"]
        self.wizard_vals = {
            "company_id": self.company.id,
            "chart_template": self.chart_template,
            "code_digits": 6,
        }

    @classmethod
    def _oss_wizard_create(cls, extra_vals):
        vals = cls.oss_wizard.default_get(list(cls.oss_wizard.fields_get()))
        vals.update(extra_vals)
        oss_wizard_id = cls.oss_wizard.create(vals)
        return oss_wizard_id

    def test_matching(self):
        # Generate EU OSS taxes
        oss_wizard_vals = {
            "company_id": self.company.id,
            "general_tax": self.tax.id,
        }
        oss_wizard = self._oss_wizard_create(oss_wizard_vals)
        oss_wizard.generate_eu_oss_taxes()

        wizard_vals = self.wizard_vals
        wizard_vals.update(update_tax=True)
        wizard = self.wizard_obj.create(wizard_vals)
        wizard.action_find_records()
        taxes_to_delete = wizard.tax_ids.filtered(lambda x: x.type == "deleted").mapped(
            "update_tax_id"
        )
        oss_taxes = self.env["account.tax"].search(
            [
                ("oss_country_id", "!=", False),
            ]
        )
        self.assertTrue(oss_taxes, "No OSS taxes found in the system")
        for tax in oss_taxes:
            self.assertNotIn(tax, taxes_to_delete)
