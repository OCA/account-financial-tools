# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import models, api


class AccountDocumentReversal(models.AbstractModel):
    _name = 'account.document.reversal'
    _description = 'Abstract Module for Document Reversal'

    @api.model
    def reverse_document_wizard(self):
        """ Return Wizard to Cancel Document """
        action = self.env.ref('account_document_reversal.'
                              'action_view_reverse_account_document')
        vals = action.read()[0]
        return vals

    @api.multi
    def action_document_reversal(self, date=None, journal_id=None):
        """ Reverse with following guildeline,
        - Check existing document state / raise warning
        - Find all related moves and unreconcile
        - Create reversed moves
        - Set state to cancel
        """
        raise NotImplementedError()
