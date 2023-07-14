# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _name = "account.payment"
    _inherit = ["account.payment", "account.document.reversal"]

    def cancel_reversal(self):
        return self.reverse_document_wizard()

    def action_draft(self):
        """ Case cancel reversal, set to draft allowed only when no moves """
        for rec in self:
            if rec.is_cancel_reversal and rec.move_line_ids:
                raise UserError(_("Cannot set to draft!"))
        return super().action_draft()

    def cancel(self):
        if any(self.mapped("is_cancel_reversal")):
            raise UserError(_("Please use cancel_reversal()"))
        return super().cancel()

    def action_document_reversal(self, date=None, journal_id=None):
        """ Reverse all moves related to this payment + set state to cancel """
        # Check document readiness
        for payment in self:
            if payment.state not in ["sent", "posted"]:
                raise UserError(
                    _("Only validated document can be cancelled (reversal)")
                )
        # Find moves to get reversed
        move_lines = self.mapped("move_line_ids").filtered(
            lambda x: x.journal_id == self.mapped("journal_id")[0]
        )
        moves = move_lines.mapped("move_id")
        # Create reverse entries
        moves._cancel_reversal(journal_id, date=date)
        # Set state cancelled and unlink with account.move
        self.write({"state": "cancelled"})
        return True
