# Copyright 2026 Saad Elbahi
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from markupsafe import Markup, escape

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError

from ..models.account_move import REVIEWER_GROUP


class AccountMoveReviewWizard(models.TransientModel):
    _name = "account.move.review.wizard"
    _description = "Reset Journal Entry to Draft with Review Notes"

    move_id = fields.Many2one(
        "account.move", string="Journal Entry", required=True, readonly=True
    )
    payment_id = fields.Many2one("account.payment", string="Payment", readonly=True)
    recipient_user_id = fields.Many2one(
        "res.users",
        string="Notify User",
        domain="[('share', '=', False), ('active', '=', True)]",
    )
    notes = fields.Text()

    def action_confirm_reset_to_draft(self):
        self.ensure_one()
        if not (self.env.su or self.env.user.has_group(REVIEWER_GROUP)):
            raise AccessError(
                _("Only entry reviewers can reset posted entries to draft.")
            )
        move = self.move_id
        if move.state != "posted":
            raise UserError(_("Only posted entries can be reset to draft."))

        if self.payment_id:
            self.payment_id.with_context(from_review_reset_wizard=True).action_draft()
        else:
            move.with_context(from_review_reset_wizard=True).button_draft()

        notes = (self.notes or "").strip()
        move.write(
            {
                "review_state": "returned",
                "reviewed_by_id": self.env.user.id,
                "reviewed_date": fields.Datetime.now(),
                "review_notes": notes or False,
            }
        )

        body = Markup(_("Entry %(move)s was reset to draft by %(reviewer)s")) % {
            "move": escape(move.name or move.display_name),
            "reviewer": escape(self.env.user.name),
        }
        if notes:
            body += Markup("<br/>") + Markup("<br/>").join(
                escape(line) for line in notes.splitlines()
            )

        partner_ids = (
            [self.recipient_user_id.partner_id.id] if self.recipient_user_id else []
        )
        target = self.payment_id or move
        email_from = (
            self.env.user.email_formatted
            or self.env.company.email_formatted
            or f"{self.env.user.name} <noreply@localhost>"
        )
        target.message_post(
            body=body,
            email_from=email_from,
            partner_ids=partner_ids,
            message_type="comment",
            subtype_xmlid="mail.mt_comment",
        )
        return {"type": "ir.actions.act_window_close"}
