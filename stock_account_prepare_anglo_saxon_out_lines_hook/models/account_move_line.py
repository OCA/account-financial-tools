# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _eligible_for_cogs(self):
        self.ensure_one()
        return (
            self.product_id.type == "product"
            and self.product_id.valuation == "real_time"
        )
