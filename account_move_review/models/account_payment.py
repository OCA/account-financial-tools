# Copyright 2026 Saad Elbahi
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import AccessError
from odoo.tools.sql import column_exists

from .account_move import REVIEWER_GROUP


class AccountPayment(models.Model):
    _inherit = "account.payment"

    move_review_state = fields.Selection(
        string="Review Status",
        related="move_id.review_state",
        store=True,
        index=True,
        readonly=True,
    )
    move_document_type = fields.Selection(
        string="Document Type",
        related="move_id.document_type",
        store=True,
        index=True,
        readonly=True,
    )
    review_move_posted = fields.Boolean(compute="_compute_review_move_posted")
    restrict_draft_to_reviewers = fields.Boolean(
        related="company_id.restrict_move_draft_to_reviewers",
    )

    def _auto_init(self):
        if not column_exists(self.env.cr, "account_payment", "move_review_state"):
            self.env.cr.execute(
                "ALTER TABLE account_payment ADD COLUMN move_review_state VARCHAR"
            )
        if not column_exists(self.env.cr, "account_payment", "move_document_type"):
            self.env.cr.execute(
                "ALTER TABLE account_payment ADD COLUMN move_document_type VARCHAR"
            )
        return super()._auto_init()

    @api.depends("move_id", "move_id.state")
    def _compute_review_move_posted(self):
        for rec in self:
            rec.review_move_posted = bool(rec.move_id and rec.move_id.state == "posted")

    def _is_move_reviewer(self):
        return self.env.su or self.env.user.has_group(REVIEWER_GROUP)

    def action_mark_move_reviewed(self):
        if not self._is_move_reviewer():
            raise AccessError(_("Only entry reviewers can mark payments as reviewed."))
        posted = self.mapped("move_id").filtered(lambda m: m.state == "posted")
        if posted:
            posted.action_mark_reviewed()
        return True

    def action_open_reset_draft_wizard(self):
        self.ensure_one()
        if not self._is_move_reviewer():
            raise AccessError(_("Only entry reviewers can reset payments to draft."))
        if self.move_id and self.move_id.state == "posted":
            recipient = self.move_id._default_review_recipient()
            return {
                "name": _("Reset to Draft"),
                "type": "ir.actions.act_window",
                "res_model": "account.move.review.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_move_id": self.move_id.id,
                    "default_payment_id": self.id,
                    "default_recipient_user_id": recipient.id if recipient else False,
                },
            }
        return self.action_draft()

    def action_draft(self):
        if (
            not self.env.context.get("bypass_move_review_draft_guard")
            and any(
                payment.state != "draft"
                and payment.company_id.restrict_move_draft_to_reviewers
                for payment in self
            )
            and not self._is_move_reviewer()
        ):
            raise AccessError(_("Only entry reviewers can reset payments to draft."))
        return super().action_draft()
