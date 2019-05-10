# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment', 'account.document.reversal']

    @api.multi
    def cancel(self):
        """ If cancel method is to reverse, use document reversal wizard """
        cancel_reversal = all(
            self.mapped('move_line_ids.move_id.journal_id.is_cancel_reversal'))
        states = self.mapped('state')
        if cancel_reversal and 'draft' not in states:
            return self.reverse_document_wizard()
        return super().cancel()

    @api.multi
    def action_document_reversal(self, date=None, journal_id=None):
        """ Reverse all moves related to this payment + set state to cancel """
        # Check document state
        if 'cancelled' in self.mapped('state'):
            raise ValidationError(
                _('You are trying to cancel the cancelled document'))
        move_lines = self.mapped('move_line_ids')
        moves = move_lines.mapped('move_id')
        # Set all moves to unreconciled
        move_lines.filtered(lambda x:
                            x.account_id.reconcile).remove_move_reconcile()
        # Important to remove relation with move.line before reverse
        move_lines.write({'payment_id': False})
        # Create reverse entries
        moves.reverse_moves(date, journal_id)
        # Set state cancelled and unlink with account.move
        self.write({'move_name': False,
                    'state': 'cancelled'})
        return True
