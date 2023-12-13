from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _eligible_for_cogs(self):
        return super()._eligible_for_cogs() or any(
            p.type == "product" and p.valuation == "real_time"
            for p in self.sale_line_ids.mapped("move_ids.product_id")
        )
