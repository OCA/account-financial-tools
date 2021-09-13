# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def write(self, vals):
        res = super().write(vals)
        if vals.get("date"):
            self.mapped("line_ids").filtered(
                lambda x: (
                    not x.date_maturity
                    and x.account_internal_type in {"receivable", "payable"}
                )
            ).write({"date_maturity": vals["date"]})
        return res
