# Copyright 2026 Saad Elbahi
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.sql import column_exists

REVIEWER_GROUP = "account_move_review.group_account_move_reviewer"

REVIEW_STATES = [
    ("not_reviewed", "Not Reviewed"),
    ("reviewed", "Reviewed"),
    ("returned", "Returned for Revision"),
]

DOCUMENT_TYPES = [
    ("documentary", "Documentary"),
    ("non_documentary", "Non-Documentary"),
]


class AccountMove(models.Model):
    _inherit = "account.move"

    review_state = fields.Selection(
        REVIEW_STATES,
        string="Review Status",
        default="not_reviewed",
        copy=False,
        index=True,
        readonly=True,
    )
    document_type = fields.Selection(
        DOCUMENT_TYPES,
        copy=False,
        index=True,
    )
    reviewed_by_id = fields.Many2one(
        "res.users", string="Reviewed By", copy=False, readonly=True
    )
    reviewed_date = fields.Datetime(string="Reviewed On", copy=False, readonly=True)
    review_notes = fields.Text(copy=False, readonly=True)
    restrict_draft_to_reviewers = fields.Boolean(
        related="company_id.restrict_move_draft_to_reviewers",
    )

    def _auto_init(self):
        if not column_exists(self.env.cr, "account_move", "review_state"):
            self.env.cr.execute(
                "ALTER TABLE account_move "
                "ADD COLUMN review_state VARCHAR DEFAULT 'not_reviewed'"
            )
        if not column_exists(self.env.cr, "account_move", "document_type"):
            self.env.cr.execute(
                "ALTER TABLE account_move ADD COLUMN document_type VARCHAR"
            )
        return super()._auto_init()

    def _is_move_reviewer(self):
        return self.env.su or self.env.user.has_group(REVIEWER_GROUP)

    def _default_review_recipient(self):
        self.ensure_one()
        root = self.env.ref("base.user_root", raise_if_not_found=False)
        creator = self.create_uid
        if creator and creator.active and not creator.share and creator != root:
            return creator
        return False

    def action_mark_reviewed(self):
        if not self._is_move_reviewer():
            raise AccessError(_("Only entry reviewers can mark entries as reviewed."))
        if any(move.state != "posted" for move in self):
            raise UserError(_("Only posted entries can be marked as reviewed."))
        moves = self.filtered(lambda m: m.review_state != "reviewed")
        if moves:
            moves.write(
                {
                    "review_state": "reviewed",
                    "reviewed_by_id": self.env.user.id,
                    "reviewed_date": fields.Datetime.now(),
                }
            )
        return True

    def action_open_reset_draft_wizard(self):
        self.ensure_one()
        if not self._is_move_reviewer():
            raise AccessError(
                _("Only entry reviewers can reset posted entries to draft.")
            )
        if self.state != "posted":
            raise UserError(
                _("Only posted entries can be reset via the review wizard.")
            )
        recipient = self._default_review_recipient()
        return {
            "name": _("Reset to Draft"),
            "type": "ir.actions.act_window",
            "res_model": "account.move.review.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_move_id": self.id,
                "default_recipient_user_id": recipient.id if recipient else False,
            },
        }

    def button_draft(self):
        if (
            not self.env.context.get("bypass_move_review_draft_guard")
            and any(
                move.state == "posted"
                and move.company_id.restrict_move_draft_to_reviewers
                for move in self
            )
            and not self._is_move_reviewer()
        ):
            raise AccessError(
                _("Only entry reviewers can reset posted entries to draft.")
            )
        res = super().button_draft()
        if not self.env.context.get("from_review_reset_wizard"):
            reviewed = self.filtered(lambda m: m.review_state == "reviewed")
            if reviewed:
                reviewed.write({"review_state": "not_reviewed"})
        return res

    def action_post(self):
        res = super().action_post()
        returned = self.filtered(lambda m: m.review_state == "returned")
        if returned:
            returned.write({"review_state": "not_reviewed"})
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

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

    def _auto_init(self):
        if not column_exists(self.env.cr, "account_move_line", "move_review_state"):
            self.env.cr.execute(
                "ALTER TABLE account_move_line "
                "ADD COLUMN move_review_state VARCHAR DEFAULT 'not_reviewed'"
            )
        if not column_exists(self.env.cr, "account_move_line", "move_document_type"):
            self.env.cr.execute(
                "ALTER TABLE account_move_line ADD COLUMN move_document_type VARCHAR"
            )
        return super()._auto_init()
