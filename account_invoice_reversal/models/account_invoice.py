# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models, _
from odoo.exceptions import ValidationError, UserError


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'account.document.reversal']

    @api.multi
    def action_invoice_cancel(self):
        """ If cancel method is to reverse, use document reversal wizard """
        if self.mapped('journal_id')[0].is_cancel_reversal:
            return self.reverse_document_wizard()
        return super().action_invoice_cancel()

    @api.multi
    def action_invoice_draft(self):
        """ If cancel method is to reverse, do not allow set to draft """
        if self.mapped('journal_id')[0].is_cancel_reversal and \
                self.mapped('move_id'):
            raise UserError(_('This document is already cancelled, '
                              'set to draft is not allowed'))
        return super().action_invoice_draft()

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
        move_lines.filtered(
            lambda x: x.account_id.reconcile).remove_move_reconcile()
        # Create reverse entries
        moves.reverse_moves(date, journal_id)
        # Set state cancelled
        self.write({'state': 'cancel'})
        return True
