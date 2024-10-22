# Copyright (C) 2020 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestModule(TransactionCase):
    def setUp(self):
        super().setUp()
        self.ACTemplate = self.env["account.chart.template"]
        self.AATemplate = self.env["account.account.template"]
        self.ATTemplate = self.env["account.tax.template"]
        self.AFPTemplate = self.env["account.fiscal.position.template"]
        self.AFPATemplate = self.env["account.fiscal.position.account.template"]
        self.AFPTTemplate = self.env["account.fiscal.position.tax.template"]

        self.receivable_type = self.env.ref("account.data_account_type_receivable")

        self.template = self.ACTemplate.create(
            {
                "name": "Chart of Account",
                "bank_account_code_prefix": "BNK",
                "cash_account_code_prefix": "CSH",
                "transfer_account_code_prefix": "TRSF",
                "currency_id": self.env.ref("base.EUR").id,
            }
        )

        self.account_template = self.AATemplate.create(
            {
                "name": "Account Template",
                "code": "CODE",
                "user_type_id": self.receivable_type.id,
                "chart_template_id": self.template.id,
            }
        )
        self.tax_template = self.ATTemplate.create(
            {
                "name": "Tax Template",
                "chart_template_id": self.template.id,
                "amount": 10.0,
            }
        )
        self.fiscal_position = self.AFPTemplate.create(
            {
                "name": "Fiscal Position",
                "chart_template_id": self.template.id,
            }
        )
        self.fiscal_position_account = self.AFPATemplate.create(
            {
                "account_src_id": self.account_template.id,
                "account_dest_id": self.account_template.id,
                "position_id": self.fiscal_position.id,
            }
        )
        self.fiscal_position_tax = self.AFPTTemplate.create(
            {
                "tax_src_id": self.tax_template.id,
                "position_id": self.fiscal_position.id,
            }
        )

    def test_tax_template(self):
        self.tax_template.active = False
        self.assertEqual(
            self.fiscal_position_tax.active,
            False,
            "Disable Tax template should disable Fiscal Position Tax",
        )

        self.fiscal_position_tax.active = True
        self.assertEqual(
            self.tax_template.active,
            True,
            "Enable Fiscal Position Tax should enable Tax Template",
        )

    def test_account_template(self):
        self.account_template.active = False
        self.assertEqual(
            self.fiscal_position_account.active,
            False,
            "Disable Account template should disable Fiscal Position Account",
        )

        self.fiscal_position_account.active = True
        self.assertEqual(
            self.account_template.active,
            True,
            "Enable Fiscal Position Account should enable Account Template",
        )
