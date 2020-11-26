# Copyright 2018-2019 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from psycopg2 import IntegrityError

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

_logger = logging.getLogger(__name__)


class TestAccountMoveTemplate(TransactionCase):
    def with_context(self, *args, **kwargs):
        context = dict(args[0] if args else self.env.context, **kwargs)
        self.env = self.env(context=context)
        return self

    def _chart_of_accounts_create(self, company, chart):
        _logger.debug("Creating chart of account")
        self.env.user.write(
            {"company_ids": [(4, company.id)], "company_id": company.id}
        )
        self.with_context(company_id=company.id, force_company=company.id)
        wizard = self.env["wizard.multi.charts.accounts"].create(
            {
                "company_id": company.id,
                "chart_template_id": chart.id,
                "code_digits": 6,
                "currency_id": self.env.ref("base.EUR").id,
                "transfer_account_id": chart.transfer_account_id.id,
            }
        )
        wizard.onchange_chart_template_id()
        wizard.execute()
        return True

    def setUp(self):
        super(TestAccountMoveTemplate, self).setUp()
        employees_group = self.env.ref("base.group_user")
        multi_company_group = self.env.ref("base.group_multi_company")
        account_user_group = self.env.ref("account.group_account_user")
        account_manager_group = self.env.ref("account.group_account_manager")
        self.company = self.env["res.company"].create({"name": "Test company"})
        self.company_2 = self.env["res.company"].create(
            {"name": "Test company 2", "parent_id": self.company.id}
        )
        self.env.user.company_ids += self.company
        self.env.user.company_ids += self.company_2

        self.user = (
            self.env["res.users"]
            .with_user(self.env.user)
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Test User",
                    "login": "test_user",
                    "email": "test@oca.com",
                    "groups_id": [
                        (
                            6,
                            0,
                            [
                                employees_group.id,
                                account_user_group.id,
                                account_manager_group.id,
                                multi_company_group.id,
                            ],
                        )
                    ],
                    "company_id": self.company.id,
                    "company_ids": [(4, self.company.id)],
                }
            )
        )

        self.user_type = self.env.ref("account.data_account_type_liquidity")

        self.chart = self.env["account.chart.template"].search([], limit=1)
        self._chart_of_accounts_create(self.company, self.chart)
        account_template = self.env["account.account.template"].create(
            {"name": "Test 1", "code": "Code_test", "user_type_id": self.user_type.id}
        )
        self.env["ir.model.data"].create(
            {
                "name": account_template.name,
                "module": "account",
                "model": "account.account.template",
                "res_id": account_template.id,
                "noupdate": 0,
            }
        )

        self.chart_2 = self.env["account.chart.template"].create(
            {
                "name": "Test Chart",
                "currency_id": self.env.ref("base.EUR").id,
                "transfer_account_id": account_template.id,
            }
        )

        account_template.chart_template_id = self.chart_2
        self.chart_2.tax_template_ids |= self.chart.tax_template_ids

        self._chart_of_accounts_create(self.company_2, self.chart_2)

        self.chart.company_id = self.company
        self.chart_2.company_id = self.company_2

        self.account_company_1 = self.env["account.account"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        self.account_journal_1 = self.env["account.journal"].create(
            {
                "name": "Journal Company 1",
                "company_id": self.company.id,
                "code": "TST",
                "type": "general",
            }
        )
        self.partner = self.env["res.partner"].create(
            {"name": "Test partner", "company_id": False}
        )
        self.partner2 = self.env["res.partner"].create(
            {"name": "Test partner 2", "company_id": False}
        )
        self.account_type = self.env["account.account.type"].create(
            {"name": "Test Tax Account Type"}
        )

        self.tax_account_id = self.env["account.account"].create(
            {
                "name": "tax account",
                "code": "TAX",
                "user_type_id": self.account_type.id,
                "company_id": self.company.id,
            }
        )
        self.tax = self.env["account.tax"].create(
            {
                "name": "Tax 10.0%",
                "amount": 10.0,
                "amount_type": "percent",
                "account_id": self.tax_account_id.id,
            }
        )

    def test_create_template(self):
        """Test that I can create a template"""
        template = (
            self.env["account.move.template"]
            .with_user(self.user)
            .create(
                {
                    "name": "Test Move Template",
                    "company_id": self.company.id,
                    "journal_id": self.account_journal_1.id,
                    "template_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "L1",
                                "sequence": 1,
                                "account_id": self.account_company_1.id,
                                "partner_id": self.partner.id,
                                "tax_line_id": self.tax.id,
                                "move_line_type": "dr",
                                "type": "input",
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "L2",
                                "sequence": 2,
                                "account_id": self.account_company_1.id,
                                "move_line_type": "cr",
                                "tax_ids": [(4, self.tax.id)],
                                "type": "input",
                            },
                        ),
                    ],
                }
            )
        )

        self.assertEquals(template.company_id, self.user.company_id)

        template_2 = template.copy()
        self.assertEquals(template_2.name, "%s (copy)" % template.name)

        wiz = (
            self.env["wizard.select.move.template"]
            .with_user(self.user)
            .create(
                {
                    "company_id": self.company.id,
                    "template_id": template.id,
                    "partner_id": self.partner2.id,
                    "date": fields.Date.today(),
                }
            )
        )
        wiz.load_lines()
        res = wiz.load_template()
        aml = self.env["account.move.line"].search(
            [("account_id", "=", self.account_company_1.id)], limit=1
        )
        self.assertEquals(res["domain"], ([("id", "in", aml.move_id.ids)]))
        aml = self.env["account.move.line"].search([("name", "=", "L1")], limit=1)
        self.assertEquals(aml.tax_line_id, self.tax)
        self.assertEquals(aml.partner_id, self.partner)
        aml = self.env["account.move.line"].search([("name", "=", "L2")], limit=1)
        self.assertEquals(aml.tax_ids[0], self.tax)
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            template_2.name = template.name
