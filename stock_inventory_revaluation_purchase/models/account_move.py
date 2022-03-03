# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        """Do automated revaluation if configured as so and if it is applicable"""
        res = super().action_post()
        if not self.company_id.revaluation_auto_created:
            return res
        if not self.check_valuation_is_needed():
            return res
        revaluation_model = self.env["stock.inventory.revaluation"]
        revaluation_action = self.button_revaluate()
        revaluation_id = revaluation_action["res_id"]
        revaluation = revaluation_model.browse(revaluation_id)
        # This will compute from the picking of the PO
        revaluation.compute_inventory_revaluation()
        # I confirm the revaluation
        revaluation.button_validate()
        return res

    def _compute_show_create_stock_revaluation_button(self):
        res = super()._compute_show_create_stock_revaluation_button()
        for rec in self:
            if rec.company_id.revaluation_auto_created:
                rec.show_create_stock_revaluation_button = False
            else:
                rec.show_create_stock_revaluation_button = True
        return res

    def check_valuation_is_needed(self, move=False):
        """This method may be needed to avoid unwanted revaluations in the concept
        of automated revaluations
        """
        self.ensure_one()
        polines = self.line_ids.mapped("purchase_line_id")
        stock_moves = self.env["stock.move"].search(
            [("purchase_line_id", "in", polines.ids)]
        )
        for move in stock_moves:
            if (
                move.product_id.cost_method not in ("fifo", "average")
                or move.state == "cancel"
                or not move.product_qty
            ):
                continue
            (
                original_value,
                price_subtotal,
                additional_value,
                bill_qty,
            ) = self._get_additional_value(move)
            if additional_value:
                return True
        return False
