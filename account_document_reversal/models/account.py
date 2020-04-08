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
        required=True,
    )
    is_cancel_reversal = fields.Boolean(
        string='Use Cancel Reversal',
        compute='_compute_is_cancel_reversal',
        help="True, when journal allow cancel entries with method is reversal",
    )
    use_different_journal = fields.Boolean(
        string='Use different journal for reversal',
        help="If checked, reversal wizard will show field Reversal Journal",
    )
    reversal_journal_id = fields.Many2one(
        'account.journal',
        string='Default Reversal Journal',
        help="Journal in this field will show in reversal wizard as default",
    )

    @api.multi
    def _compute_is_cancel_reversal(self):
        for rec in self:
            rec.is_cancel_reversal = \
                rec.update_posted and rec.cancel_method == 'reversal'
