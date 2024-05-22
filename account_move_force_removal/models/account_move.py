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
            self._check_can_be_deleted(states=["posted"], check_group=False)
            cancelled_moves = self.filtered(lambda m: m.state == "cancel")
            super(AccountMove, cancelled_moves.with_context(force_delete=True)).unlink()
        else:
            self._check_can_be_deleted(states=["cancel"])
        return super(AccountMove, self - cancelled_moves).unlink()

    def _check_can_be_deleted(self, states, check_group=True):

        for move in self:
            move_journal = move.journal_id
            move_has_old_sequence = hasattr(move_journal, "sequence_id") or hasattr(
                move_journal, "refund_sequence_id"
            )
            if (
                move.state in states
                and move_has_old_sequence
                and (check_group or move.name != "/")
                and (move_journal.sequence_id or move_journal.refund_sequence_id)
            ):
                raise UserError(
                    _("You cannot delete an entry which has been posted once.")
                )
        return True
