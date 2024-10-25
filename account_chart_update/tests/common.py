# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common, tagged


@tagged("-at_install", "post_install")
class TestAccountChartUpdateCommon(common.TransactionCase):
    @classmethod
    def _create_xml_id(cls, record):
        return cls.env["ir.model.data"].create(
            {
                "module": "account_chart_update",
                "name": "{}-{}".format(record._table, record.id),
                "model": record._name,
                "res_id": record.id,
            }
        )

    @classmethod
    def _create_account_tmpl(cls, name, code, account_type, chart_template):
        record = cls.env["account.account.template"].create(
            {
                "name": name,
                "code": code,
                "account_type": account_type,
                "chart_template_id": chart_template and chart_template.id,
            }
        )
        cls._create_xml_id(record)
        return record

    @classmethod
    def _create_tax_tmpl(cls, name, chart_template):
        record = cls.env["account.tax.template"].create(
            {
                "name": name,
                "amount": 0,
                "chart_template_id": chart_template.id,
                "tax_group_id": cls.env.ref("account.tax_group_taxes").id,
                "refund_repartition_line_ids": [
                    (0, 0, {"repartition_type": "base", "factor_percent": 100.0}),
                    (0, 0, {"repartition_type": "tax", "factor_percent": 100.0}),
                    (0, 0, {"repartition_type": "tax", "factor_percent": 100.0}),
                ],
                "invoice_repartition_line_ids": [
                    (0, 0, {"repartition_type": "base", "factor_percent": 100.0}),
                    (0, 0, {"repartition_type": "tax", "factor_percent": 100.0}),
                    (0, 0, {"repartition_type": "tax", "factor_percent": 100.0}),
                ],
            }
        )
        cls._create_xml_id(record)
        return record

    def _create_tax_template_with_account(self, name, chart_template, account):
        record = self.env["account.tax.template"].create(
            {
                "name": name,
                "amount": 0,
                "chart_template_id": chart_template.id,
                "tax_group_id": self.env.ref("account.tax_group_taxes").id,
                "refund_repartition_line_ids": [
                    (0, 0, {"repartition_type": "base", "factor_percent": 100.0}),
                    (
                        0,
                        0,
                        {
                            "repartition_type": "tax",
                            "factor_percent": 100.0,
                            "account_id": account.id,
                        },
                    ),
                ],
                "invoice_repartition_line_ids": [
                    (0, 0, {"repartition_type": "base", "factor_percent": 100.0}),
                    (
                        0,
                        0,
                        {
                            "repartition_type": "tax",
                            "factor_percent": 100.0,
                            "account_id": account.id,
                        },
                    ),
                ],
            }
        )
        self._create_xml_id(record)
        return record

    @classmethod
    def _create_fp_tmpl(cls, name, chart_template):
        record = cls.env["account.fiscal.position.template"].create(
            {"name": name, "chart_template_id": chart_template.id}
        )
        cls._create_xml_id(record)
        return record

    def _get_model_data(self, record):
        return self.env["ir.model.data"].search(
            [("model", "=", record._name), ("res_id", "=", record.id)]
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.account_template = cls._create_account_tmpl(
            "Test", "100000", "income", False
        )
        cls.chart_template = cls.env["account.chart.template"].create(
            {
                "name": "Test account_chart_update chart",
                "currency_id": cls.env.ref("base.EUR").id,
                "code_digits": 6,
                "cash_account_code_prefix": "570",
                "bank_account_code_prefix": "572",
                "transfer_account_code_prefix": "100000",
                "property_account_receivable_id": cls.account_template.id,
                "property_account_payable_id": cls.account_template.id,
                "property_account_expense_categ_id": cls.account_template.id,
                "property_account_income_categ_id": cls.account_template.id,
            }
        )
        cls.account_template.chart_template_id = cls.chart_template.id
        cls.account_template_pl = cls._create_account_tmpl(
            "Undistributed Profits/Losses",
            "999999",
            "equity",
            cls.chart_template,
        )
        cls.tax_template = cls._create_tax_tmpl("Test tax", cls.chart_template)
        cls.fp_template = cls._create_fp_tmpl("Test fp", cls.chart_template)
        cls.fp_template_tax = cls.env["account.fiscal.position.tax.template"].create(
            {"tax_src_id": cls.tax_template.id, "position_id": cls.fp_template.id}
        )
        cls._create_xml_id(cls.fp_template_tax)
        cls.fp_template_account = cls.env[
            "account.fiscal.position.account.template"
        ].create(
            {
                "account_src_id": cls.account_template.id,
                "account_dest_id": cls.account_template.id,
                "position_id": cls.fp_template.id,
            }
        )
        cls._create_xml_id(cls.fp_template_account)
        cls.tax_group = cls.env["account.tax.group"].create({"name": "Test tax group"})
        cls.account_tag_1 = cls.env["account.account.tag"].create(
            {"name": "Test account tag 1"}
        )
        cls.account_tag_2 = cls.env["account.account.tag"].create(
            {"name": "Test account tag 2"}
        )
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test account_chart_update company",
                "currency_id": cls.chart_template.currency_id.id,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        chart_by_company_user = cls.chart_template.with_company(cls.company)
        chart_by_company_user.try_loading()
        cls.tax = cls.env["account.tax"].search(
            [
                ("name", "=", cls.tax_template.name),
                ("company_id", "=", cls.company.id),
            ]
        )
        cls.account = cls.env["account.account"].search(
            [
                ("code", "=", cls.account_template.code),
                ("company_id", "=", cls.company.id),
            ]
        )
        cls.fp = cls.env["account.fiscal.position"].search(
            [("name", "=", cls.fp_template.name), ("company_id", "=", cls.company.id)]
        )
        # Prepare wizard values
        cls.wizard_obj = cls.env["wizard.update.charts.accounts"]
        cls.wizard_vals = {
            "company_id": cls.company.id,
            "chart_template_id": cls.chart_template.id,
            "code_digits": 6,
            "lang": "en_US",
        }
