# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models, _
from odoo.exceptions import ValidationError, UserError


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'account.document.reversal']

    @api.multi
    def action_invoice_cancel(self):
        """ If cancel method is to reverse, use document reversal wizard
        * Draft invoice, fall back to standard invoice cancel
        * Non draft, must be fully open (not even partial reconciled) to cancel
        """
        cancel_reversal = all(self.mapped('journal_id.is_cancel_reversal'))
        states = self.mapped('state')
        if cancel_reversal and 'draft' not in states:
            if not all(st == 'open' for st in states) or \
                    (self.mapped('move_id.line_ids.matched_debit_ids') |
                     self.mapped('move_id.line_ids.matched_credit_ids')):
                raise UserError(
                    _('Only fully unpaid invoice can be cancelled.\n'
                      'To cancel this invoice, make sure all payment(s) '
                      'are also cancelled.'))
            return self.reverse_document_wizard()
        return super().action_invoice_cancel()

    @api.multi
    def action_document_reversal(self, date=None, journal_id=None):
        """ Reverse all moves related to this invoice + set state to cancel """
        # Check document state
        if 'cancel' in self.mapped('state'):
            raise ValidationError(
                _('You are trying to cancel the cancelled document'))
        MoveLine = self.env['account.move.line']
        move_lines = MoveLine.search([('invoice_id', 'in', self.ids)])
        moves = move_lines.mapped('move_id')
        # Set all moves to unreconciled
        move_lines.filtered(lambda x:
                            x.account_id.reconcile).remove_move_reconcile()
        # Important to remove relation with move.line before reverse
        move_lines.write({'invoice_id': False})
        # Create reverse entries
        moves.reverse_moves(date, journal_id)
        # Set state cancelled and unlink with account.move
        self.write({'move_id': False,
                    'move_name': False,
                    'reference': False,
                    'state': 'cancel'})
        return True
