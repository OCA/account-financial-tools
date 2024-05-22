# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def unlink(self):
        cancelled_moves = self.env["account.move"]
        if self.env.user.has_group(
            "account_move_force_removal.group_account_move_force_removal"
        ):
            for move in self:
                if (
                    move.state == "posted"
                    and move.journal_id.sequence_id
                    or move.journal_id.refund_sequence_id
                ):
                    raise UserError(
                        _("You cannot delete an entry which has been posted once.")
                    )
            cancelled_moves = self.filtered(lambda m: m.state == "cancel")
            super(AccountMove, cancelled_moves.with_context(force_delete=True)).unlink()
        return super(AccountMove, self - cancelled_moves).unlink()
