# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models, _
from odoo.exceptions import ValidationError


class AccountPaymentIntransit(models.Model):
    _name = 'account.payment.intransit'
    _inherit = ['account.payment.intransit', 'account.document.reversal']

    @api.multi
    def action_intransit_cancel(self):
        """ If cancel method is to reverse, use document reversal wizard
        * Draft Payment Intransit, fall back to standard cancel
        * Non draft to cancel
        """
        cancel_reversal = \
            all(self.mapped('bank_journal_id.is_cancel_reversal'))
        states = self.mapped('state')
        if cancel_reversal and 'draft' not in states:
            return self.reverse_document_wizard()
        return super().action_intransit_cancel()

    @api.multi
    def action_document_reversal(self, date=None, journal_id=None):
        """ Reverse all moves related to this
            intransit line + set state to cancel """
        # Check document state
        if 'cancel' in self.mapped('state'):
            raise ValidationError(
                _('You are trying to cancel the cancelled document'))

        # Set all moves to unreconciled
        if self.move_id:
            # Create reverse entries
            self.move_id.reverse_moves(date, journal_id)

        # Set state cancelled and unlink with account.move
        self.write({'move_id': False, 'state': 'cancel'})
        return True
