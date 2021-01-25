# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(
        selection_add=[('amlse',
                        'AccountMoveLineSearchExtension')])

    @api.model
    def postprocess(self, model, node, view_id, in_tree_view, model_fields):
        if node.tag == 'amlse':
            in_tree_view = True
        return super().postprocess(model, node, view_id, in_tree_view,
                                   model_fields)
