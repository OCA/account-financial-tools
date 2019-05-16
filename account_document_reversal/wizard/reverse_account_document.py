# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, fields, api


class ReverseAccountDocument(models.TransientModel):
    """
    Document reversal wizard, it cancel by reverse document journal entries
    """
    _name = 'reverse.account.document'
    _description = 'Account Document Reversal'

    date = fields.Date(
        string='Reversal date',
        default=fields.Date.context_today,
        required=True)
    journal_id = fields.Many2one(
        'account.journal',
        string='Use Specific Journal',
        help='If empty, uses the journal of the journal entry to be reversed.')

    @api.multi
    def action_cancel(self):
        model = self._context.get('active_model')
        active_ids = self._context.get('active_ids')
        documents = self.env[model].browse(active_ids)
        documents.action_document_reversal(self.date, self.journal_id)
        return {'type': 'ir.actions.act_window_close'}
