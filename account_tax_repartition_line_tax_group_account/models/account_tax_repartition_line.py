# Copyright 2020 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class AccountTaxRepartitionLine(models.Model):
    _inherit = "account.tax.repartition.line"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            account_id = vals.get("account_id")
            repartition_type = vals.get("repartition_type")
            tax_id = vals.get("tax_id")
            if not account_id and tax_id and repartition_type == "tax":
                tax = self.env["account.tax"].browse(tax_id)
                def_acc = tax.tax_group_id.with_company(
                    tax.company_id
                ).property_repartition_line_account_id
                if def_acc:
                    vals["account_id"] = def_acc.id
        return super().create(vals_list)
