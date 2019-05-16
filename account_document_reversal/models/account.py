# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    cancel_method = fields.Selection(
        [('normal', 'Normal (delete journal entries if exists)'),
         ('reversal', 'Reversal (create reversed journal entries)')],
        string='Cancel Method',
        default='normal',
        required=True)
    is_cancel_reversal = fields.Boolean(
        string='Use Cancel Reversal',
        compute='_compute_is_cancel_reversal',
        help="True, when journal allow cancel entries with method is reversal")

    @api.multi
    def _compute_is_cancel_reversal(self):
        for rec in self:
            rec.is_cancel_reversal = \
                rec.update_posted and rec.cancel_method == 'reversal'
