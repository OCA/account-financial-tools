# Copyright 2016-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        """Invoked when validating the invoices."""
        self.mapped("invoice_line_ids").create_auto_spread()
        res = super().action_post()
        spreads = self.mapped("invoice_line_ids.spread_id")
        spreads.compute_spread_board()
        # On posting of spread moves. Find their related spreads to reconcile
        move_spreads = self.env["account.spread"].search(
            [("line_ids.move_id", "in", self.ids)]
        )
        spreads += move_spreads
        spreads.reconcile_spread_moves()
        return res

    def button_cancel(self):
        """Cancel the spread lines and their related moves when
        the invoice is canceled."""
        spread_lines = self.mapped("invoice_line_ids.spread_id.line_ids")
        moves = spread_lines.mapped("move_id")
        moves.line_ids.remove_move_reconcile()
        moves.filtered(lambda move: move.state == "posted").button_draft()
        moves.with_context(force_delete=True).unlink()
        spread_lines.unlink()
        res = super().button_cancel()
        return res

    def _get_unbalanced_moves(self, container):
        if not self.env.context.get("skip_unique_sequence_number"):
            return super()._get_unbalanced_moves(container)
