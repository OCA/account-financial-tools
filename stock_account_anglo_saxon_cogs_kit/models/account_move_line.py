# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _eligible_for_cogs(self):
        return super()._eligible_for_cogs() or any(
            p.type == "product" and p.valuation == "real_time"
            for p in self.sale_line_ids.mapped("move_ids.product_id")
        )

    def _can_use_stock_accounts(self):
        return super()._can_use_stock_accounts() or any(
            p.type == "product" and p.valuation == "real_time"
            for p in self.purchase_line_id.mapped("move_ids.product_id")
        )
