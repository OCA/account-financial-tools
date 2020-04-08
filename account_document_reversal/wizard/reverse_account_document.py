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
        required=True,
    )
    use_different_journal = fields.Boolean(
        string='Use different journal for reversal',
        help="Checked, if the journal of underlineing document is checked."
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Reversal Journal',
        help='If empty, uses the journal of the journal entry to be reversed.',
    )

    @api.model
    def default_get(self, default_fields):
        model = self._context.get('active_model')
        active_ids = self._context.get('active_ids')
        documents = self.env[model].browse(active_ids)
        res = super().default_get(default_fields)
        if documents:
            if 'journal_id' in documents[0]:
                journal = documents[0].journal_id
                if journal.use_different_journal:
                    res['use_different_journal'] = True
                    res['journal_id'] = journal.reversal_journal_id.id
        return res

    @api.multi
    def action_cancel(self):
        model = self._context.get('active_model')
        active_ids = self._context.get('active_ids')
        documents = self.env[model].browse(active_ids)
        documents.action_document_reversal(self.date, self.journal_id)
        return {'type': 'ir.actions.act_window_close'}
