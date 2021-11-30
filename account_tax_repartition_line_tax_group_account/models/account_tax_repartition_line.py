# Copyright 2020 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class AccountTaxRepartitionLine(models.Model):
    _inherit = "account.tax.repartition.line"

    @api.model
    def create(self, vals):
        account_id = vals.get("account_id", "")
        invoice_tax_id = vals.get("invoice_tax_id", "")
        refund_tax_id = vals.get("refund_tax_id", "")
        repartition_type = vals.get("repartition_type", "")
        tax_id = invoice_tax_id or refund_tax_id
        if not account_id and tax_id and repartition_type == "tax":
            tax = self.env["account.tax"].browse(tax_id)
            def_acc = tax.tax_group_id.with_context(
                force_company=tax.company_id.id
            ).property_repartition_line_account_id
            if def_acc:
                vals["account_id"] = def_acc.id
        return super(AccountTaxRepartitionLine, self).create(vals)
