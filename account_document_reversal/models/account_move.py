# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "account.document.reversal"]

    cancel_reversal = fields.Boolean(
        string="Cancel Reversal",
        default=False,
        copy=False,
        help="This document is being cancelled by using reversal method",
    )
    reverse_entry_id = fields.Many2one(
        comodel_name="account.move",
        string="Reversed by",
        compute="_compute_reverse_entry_id",
        help="The move that reverse this move (opposite of reversed_entry_id)",
    )

    def _compute_reverse_entry_id(self):
        res = self.sudo().search_read(
            fields=["id", "reversed_entry_id"],
            domain=[("reversed_entry_id", "in", self.ids)],
        )
        reverse_entries = {x["reversed_entry_id"][0]: x["id"] for x in res}
        for move in self:
            move.reverse_entry_id = reverse_entries.get(move.id, False)

    def button_cancel_reversal(self):
        return self.reverse_document_wizard()

    def button_draft(self):
        for rec in self:
            if rec.is_cancel_reversal and rec.state != "cancel":
                raise UserError(_("Cannot set to draft!"))
        return super().button_draft()

    def button_cancel(self):
        if any(self.mapped("is_cancel_reversal")):
            raise UserError(_("Please use button_cancel_reversal()"))
        return super().button_cancel()

    def action_document_reversal(self, date=None, journal_id=None):
        # Check document readiness
        valid_state = (
            len(self.mapped("state")) == 1
            and list(set(self.mapped("state")))[0] == "posted"
        )
        if not valid_state:
            raise UserError(_("Only posted document can be cancelled (reversal)"))
        if self.mapped("line_ids.matched_debit_ids") | self.mapped(
            "line_ids.matched_credit_ids"
        ):
            raise UserError(
                _(
                    "Only fully unpaid invoice can be cancelled.\n"
                    "To cancel this invoice, make sure all payment(s) "
                    "are also cancelled."
                )
            )
        # Create reverse entries
        self._cancel_reversal(journal_id, date=date)
        return True

    def _cancel_reversal(self, journal_id, date=None):
        self.mapped("line_ids").filtered(
            lambda x: x.account_id.reconcile
        ).remove_move_reconcile()
        Reversal = self.env["account.move.reversal"].with_context(
            active_ids=self.ids, active_model="account.move"
        )
        res = Reversal.default_get([])
        res.update(
            {"journal_id": journal_id, "refund_method": "cancel", "move_type": "entry"}
        )
        if date:
            res["date"] = date
        reversal = Reversal.create(res)
        reversal.with_context(cancel_reversal=True).reverse_moves()

    def _reverse_moves(self, default_values_list=None, cancel=False):
        """ Set flag on the moves and the reversal moves being reversed """
        if self._context.get("cancel_reversal"):
            self.write({"cancel_reversal": True})
        reverse_moves = super()._reverse_moves(default_values_list, cancel)
        if self._context.get("cancel_reversal"):
            reverse_moves.write({"cancel_reversal": True})
        return reverse_moves

    def _reverse_move_vals(self, default_values, cancel=True):
        """ Reverse with cancel reversal, always use move_type = entry """
        if self._context.get("cancel_reversal"):
            default_values.update({"type": "entry"})
        return super()._reverse_move_vals(default_values, cancel)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def remove_move_reconcile(self):
        """ Freeze move with cancel_reversal = True, disallow unreconcile """
        if not self._context.get("cancel_reversal") and any(
            self.mapped("move_id").mapped("cancel_reversal")
        ):
            raise UserError(
                _(
                    "This document was cancelled and freozen,\n"
                    "unreconcilation not allowed."
                )
            )
        return super().remove_move_reconcile()
