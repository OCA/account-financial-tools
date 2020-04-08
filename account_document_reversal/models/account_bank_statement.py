# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _name = 'account.bank.statement.line'
    _inherit = ['account.bank.statement.line', 'account.document.reversal']

    @api.multi
    def button_cancel_reconciliation(self):
        """ If cancel method is to reverse, use document reversal wizard """
        cancel_reversal = all(self.mapped('journal_entry_ids.move_id.'
                                          'journal_id.is_cancel_reversal'))
        states = self.mapped('statement_id.state')
        if cancel_reversal:
            if not all(st == 'open' for st in states):
                raise UserError(
                    _('Only new bank statement can be cancelled'))
            return self.reverse_document_wizard()
        return super().button_cancel_reconciliation()

    @api.multi
    def action_document_reversal(self, date=None, journal_id=None):
        """ Reverse all moves related to this statement + delete payment """
        # This part is from button_cancel_reconciliation()
        aml_to_unbind = self.env['account.move.line']
        aml_to_cancel = self.env['account.move.line']
        payment_to_unreconcile = self.env['account.payment']
        payment_to_cancel = self.env['account.payment']
        for st_line in self:
            aml_to_unbind |= st_line.journal_entry_ids
            for line in st_line.journal_entry_ids:
                payment_to_unreconcile |= line.payment_id
                if st_line.move_name and \
                        line.payment_id.payment_reference == st_line.move_name:
                    # there can be several moves linked to a statement line but
                    # maximum one created by the line itself
                    aml_to_cancel |= line
                    payment_to_cancel |= line.payment_id
        aml_to_unbind = aml_to_unbind - aml_to_cancel
        if aml_to_unbind:
            aml_to_unbind.write({'statement_line_id': False})
        payment_to_unreconcile = payment_to_unreconcile - payment_to_cancel
        if payment_to_unreconcile:
            payment_to_unreconcile.unreconcile()
        # --

        # Set all moves to unreconciled
        aml_to_cancel.filtered(lambda x:
                               x.account_id.reconcile).remove_move_reconcile()
        moves = aml_to_cancel.mapped('move_id')
        # Important to remove relation with move.line before reverse
        aml_to_cancel.write({'payment_id': False,
                             'statement_id': False,
                             'statement_line_id': False})
        # Create reverse entries
        moves.reverse_moves(date, journal_id)
        # Delete related payments
        if payment_to_cancel:
            payment_to_cancel.unlink()
        # Unlink from statement line
        self.write({'move_name': False})
        return True
