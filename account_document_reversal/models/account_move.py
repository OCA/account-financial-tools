# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'account.document.reversal']

    is_cancel_reversal = fields.Boolean(
        string='Use Cancel Reversal',
        related='journal_id.is_cancel_reversal',
    )

    @api.multi
    def button_cancel(self):
        """ Do not allow using this button for cancel with reversal """
        cancel_reversal = any(self.mapped('is_cancel_reversal'))
        if cancel_reversal:
            raise ValidationError(
                _('This action is not allowed for cancel with reversal.\n'
                  'Please use Reverse Entry.'))
        return super().button_cancel()
