# Copyright 2020 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import odoo.tests.common as common


class TestAccountTaxRepartitionLineTaxGroupAccount(common.TransactionCase):
    def setUp(self):
        super().setUp()
        res_users_account_manager = self.env.ref("account.group_account_manager")
        partner_manager = self.env.ref("base.group_partner_manager")
        self.env.user.write(
            {"groups_id": [(6, 0, [res_users_account_manager.id, partner_manager.id])]}
        )
        self.sales_tax_account = self.env["account.account"].create(
            {
                "code": "salestax",
                "name": "sales_tax",
                "account_type": "liability_current",
                "reconcile": False,
            }
        )
        self.sales_tax_group = self.env["account.tax.group"].create(
            {
                "name": "Sales Tax Group",
                "property_repartition_line_account_id": self.sales_tax_account.id,
            }
        )

    def test_default_account(self):
        tax = self.env["account.tax"].create(
            {
                "name": "sales tax",
                "type_tax_use": "sale",
                "amount_type": "percent",
                "amount": 5.00,
                "tax_exigibility": "on_invoice",
                "tax_group_id": self.sales_tax_group.id,
            }
        )
        irls = tax.mapped("invoice_repartition_line_ids")
        irl_accs = irls.filtered(lambda rl: rl.repartition_type == "tax").mapped(
            "account_id"
        )
        self.assertEqual(irl_accs[0], self.sales_tax_account)
        rrls = tax.mapped("refund_repartition_line_ids")
        rrl_accs = rrls.filtered(lambda rl: rl.repartition_type == "tax").mapped(
            "account_id"
        )
        self.assertEqual(rrl_accs[0], self.sales_tax_account)
