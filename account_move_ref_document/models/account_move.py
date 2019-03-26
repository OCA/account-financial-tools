# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    document_id = fields.Reference(
        selection='_selection_model',
        string='Document',
        help="Reference to the document that create this Account Move",
    )
    document_ref = fields.Char(
        string='Document Ref',
        help="Reference to the document that create this Account Move",
    )

    @api.model
    def _selection_model(self):
        models = self.env['ir.model'].search([])
        return [(model.model, model.name) for model in models]

    @api.multi
    def post(self, invoice=False):
        """ Only when posted, stamp document_ref """
        res = super().post(invoice=invoice)
        for move in self.filtered('document_id'):
            move.document_ref = move.document_id.display_name
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    document_id = fields.Reference(
        selection='_selection_model',
        string='Document',
        related='move_id.document_id',
        store=True,
        help="Reference to the document that create this Account Move Line",
    )
    document_ref = fields.Char(
        string='Document Ref',
        related='move_id.document_ref',
        store=True,
        help="Reference to the document that create this Account Move Line",
    )

    @api.model
    def _selection_model(self):
        models = self.env['ir.model'].search([])
        return [(model.model, model.name) for model in models]
