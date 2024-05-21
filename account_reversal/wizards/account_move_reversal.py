# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class AccountMoveReversal(models.TransientModel):

    _inherit = "account.move.reversal"

    line_reason = fields.Char(
        help="Prefix that will be added to the 'Name' of the reversal account "
        "entry items. If empty, Odoo uses the same name of the move "
        "line to reverse. (NOTE: A space is added after the prefix)."
    )

    def reverse_moves(self):
        res = super().reverse_moves()
        if self.line_reason:
            for line in self.new_move_ids.line_ids:
                if line.name:
                    line.name = " : ".join([self.line_reason, line.name])
                else:
                    line.name = self.line_reason
        return res
