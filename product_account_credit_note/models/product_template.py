# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

ACCOUNT_DOMAIN = "[('deprecated', '=', False), ('company_id', '=', current_company_id)]"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    credit_note_account_id = fields.Many2one(
        "account.account",
        help="Keep empty to use the default value from the category or the income account.",
        string="Credit Note Account",
        domain=ACCOUNT_DOMAIN,
        company_dependent=True,
    )

    def _get_product_accounts(self):
        res = super()._get_product_accounts()
        if self.env.context.get("default_move_type", False) == "out_refund":
            if (
                self.credit_note_account_id
                or self.categ_id.credit_note_account_categ_id
            ):
                res["income"] = (
                    self.credit_note_account_id
                    or self.categ_id.credit_note_account_categ_id
                )
        return res
