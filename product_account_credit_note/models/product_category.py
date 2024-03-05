# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

ACCOUNT_DOMAIN = "[('deprecated', '=', False), ('company_id', '=', current_company_id)]"


class ProductCategory(models.Model):
    _inherit = "product.category"

    credit_note_account_categ_id = fields.Many2one(
        "account.account",
        help="This account will be used when validating a customer credit note.",
        string="Credit Note Account",
        domain=ACCOUNT_DOMAIN,
        company_dependent=True,
    )
