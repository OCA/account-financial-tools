# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _name = "account.bank.statement.line"
    _inherit = ["account.bank.statement.line", "account.document.reversal"]

    def button_cancel_reconciliation(self):
        """ If cancel method is to reverse, use document reversal wizard """
        cancel_reversal = all(
            self.mapped("journal_entry_ids.move_id.journal_id.is_cancel_reversal")
        )
        states = self.mapped("statement_id.state")
        if cancel_reversal:
            if not all(st == "open" for st in states):
                raise UserError(_("Only new bank statement can be cancelled"))
            return self.reverse_document_wizard()
        return super().button_cancel_reconciliation()

    def action_document_reversal(self, date=None, journal_id=None):
        """ Reverse all moves related to this statement + delete payment """
        # This part is from button_cancel_reconciliation()
        aml_to_unbind = self.env["account.move.line"]
        payments_to_revert = self.env["account.payment"]
        for st_line in self:
            aml_to_unbind |= st_line.journal_entry_ids
            for line in st_line.journal_entry_ids:
                if (
                    st_line.move_name
                    and line.payment_id.payment_reference == st_line.move_name
                ):
                    payments_to_revert |= line.payment_id
        aml_to_unbind = aml_to_unbind
        if aml_to_unbind:
            aml_to_unbind.write({"statement_line_id": False})
        for payment in payments_to_revert:
            payment.unreconcile()
            payment.action_document_reversal(date=date, journal_id=journal_id)
        self.write({"move_name": False})
        return True
