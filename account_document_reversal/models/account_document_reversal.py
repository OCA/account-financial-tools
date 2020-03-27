# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models, fields


class AccountDocumentReversal(models.AbstractModel):
    _name = "account.document.reversal"
    _description = "Abstract Module for Document Reversal"

    is_cancel_reversal = fields.Boolean(
        string="Use Cancel Reversal",
        compute="_compute_is_cancel_reversal",
    )
    # reversal_move_ids = fields.Many2many(
    #     comodel_name="account.move",
    #     help="Cancelled journal entries",
    # )

    def _compute_is_cancel_reversal(self):
        for rec in self:
            if "journal_id" in rec:
                rec.is_cancel_reversal = rec.journal_id.is_cancel_reversal
            else:
                rec.is_cancel_reversal = False

    @api.model
    def reverse_document_wizard(self):
        """ Return Wizard to Cancel Document """
        action = self.env.ref(
            "account_document_reversal." "action_view_reverse_account_document"
        )
        vals = action.read()[0]
        return vals

    def action_document_reversal(self, date=None, journal_id=None):
        """ Reverse with following guildeline,
        - Check existing document state / raise warning
        - Find all related moves and unreconcile
        - Create reversed moves
        - Set state to cancel
        """
        raise NotImplementedError()
