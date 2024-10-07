# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):

    _inherit = "account.move"

    reset_to_draft_bypassed = fields.Boolean(
        readonly=True,
        help="If this is checked, this record has been reset to draft by bypassing the "
        "warning about stock valuations.",
    )
    allow_draft_button_bypass = fields.Boolean(
        compute="_compute_allow_draft_button_bypass",
        help="This is a technical field in order to show the reset to draft button if user"
        "has the right to.",
    )

    @api.depends("show_reset_to_draft_button", "restrict_mode_hash_table", "state")
    def _compute_allow_draft_button_bypass(self):
        user_has_access = self.env.user.has_group(
            "stock_account_move_show_draft_button.can_bypass_draft_button"
        )
        for move in self:
            if (
                user_has_access
                and not move.show_reset_to_draft_button
                and not move.restrict_mode_hash_table
                and move.state in ("posted", "cancel")
            ):
                move.allow_draft_button_bypass = True
            else:
                move.allow_draft_button_bypass = False

    def action_button_draft_bypass(self):
        self.ensure_one()
        if not self.allow_draft_button_bypass:
            raise UserError(
                _(
                    "You don't have the right to bypass the draft state restriction! "
                    "Please ask your administrator."
                )
            )
        self.button_draft()
        self.write({"reset_to_draft_bypassed": True})
        self._log_to_draft_bypass()

    def _log_to_draft_bypass(self):
        """
        Post a message on account move that the user had bypassed the
        warning about resetting to draft.
        """
        self.ensure_one()
        body = _(
            "The move was reset to draft by bypassing the warning about stock valuations."
        )
        self.message_post(body=body)
