# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class AccountMoveReversal(models.TransientModel):

    _inherit = "account.move.reversal"

    line_reason = fields.Char(
        help="Prefix that will be added to the Label of the reversal "
        "entry items. If empty, Odoo uses the same label as the reversed "
        "item. (NOTE: a space and a colon added after the prefix)."
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
