# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def _check_valuation_price_change(self, vals) -> None:
        """
        If feature is enabled, check if account move line price try to be changed
        if stock valuations have already been generated.
        """
        if "price_unit" in vals:
            for line in self:
                if (
                    line.move_id.company_id.restrict_account_move_line_change_after_valuation
                    and line.stock_valuation_layer_ids
                ):
                    raise UserError(
                        _(
                            "You cannot change the price of the accounting entry"
                            " %(line_name)s (%(move_name)s) as inventory valuations "
                            "have already been generated for that line!"
                            "Ask your administrator",
                            line_name=line.display_name,
                            move_name=line.move_id.display_name,
                        )
                    )

    def write(self, vals):
        self._check_valuation_price_change(vals)
        return super().write(vals)
