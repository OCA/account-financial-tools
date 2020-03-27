# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "account.document.reversal"]

    cancel_reversal = fields.Boolean(
        string="Cancel Reversal",
        default=False, copy=False,
        help="This document is being cancelled by using reversal method",
    )

    def button_cancel_reversal(self):
        return self.reverse_document_wizard()

    def button_draft(self):
        for rec in self:
            if rec.is_cancel_reversal and rec.state != "cancel":
                raise UserError(_("Cannot set to draft!"))
        return super().button_draft()

    def action_document_reversal(self, date=None, journal_id=None):
        # Check document readiness
        valid_state = len(self.mapped("state")) == 1 and \
            list(set(self.mapped("state")))[0] == "posted"
        if not valid_state:
            raise UserError(
                _("Only posted document can be cancelled (reversal)"))
        if self.mapped("line_ids.matched_debit_ids") | self.mapped("line_ids.matched_credit_ids"):
            raise UserError(
                _("Only fully unpaid invoice can be cancelled.\n"
                  "To cancel this invoice, make sure all payment(s) "
                  "are also cancelled."))
        # Create reverse entries
        self._cancel_reversal(journal_id)
        return True

    def _cancel_reversal(self, journal_id):
        self.mapped("line_ids").filtered(
            lambda x: x.account_id.reconcile).remove_move_reconcile()
        Reversal = self.env["account.move.reversal"]
        ctx = {"active_ids": self.ids, "active_model": "account.move"}
        res = Reversal.with_context(ctx).default_get([])
        res.update({"journal_id": journal_id,
                    "refund_method": "cancel",
                    "move_type": "entry", })
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
        """ For move with cancel_reversal = True, freeze it """
        if not self._context.get("cancel_reversal") and \
                any(self.mapped("move_id").mapped("cancel_reversal")):
            raise UserError(_("This document was cancelled and freezed,\n"
                              "unreconcilation not allowed."))
        return super().remove_move_reconcile()
