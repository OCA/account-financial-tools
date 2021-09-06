# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("date_maturity"):
                account = self.env["account.account"].browse(vals.get("account_id"))
                if account.internal_type in {"receivable", "payable"}:
                    move = self.env["account.move"].browse(vals.get("move_id"))
                    vals["date_maturity"] = move.date
        return super().create(vals_list)
