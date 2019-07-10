# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAssetCompute(models.TransientModel):
    _name = 'account.asset.edit.salvage'
    _description = 'Editing salvage value when created from invoice'

    asset_id = fields.Many2one(
        comodel_name='account.asset',
        default=lambda self: self.env['account.asset'].search([
            ('id', 'in', self._context.get('active_ids', []))
        ])
    )

    salvage_value = fields.Float(
        default=lambda self: self._default_salvage_value(),
        required=True,
        help="Update salvage value that created from invoice"
    )

    @api.multi
    def _default_salvage_value(self):
        model = self._context.get('active_model')
        active_ids = self._context.get('active_ids')
        documents = self.env[model].browse(active_ids)
        return documents.salvage_value

    @api.multi
    def action_confirm(self):
        model = self._context.get('active_model')
        active_ids = self._context.get('active_ids')
        documents = self.env[model].browse(active_ids)
        if self.salvage_value < 0 \
                or self.salvage_value > documents.purchase_value:
            raise ValidationError(_(
                'Can not update %.2f to Salvage Value.'
                ) % (self.salvage_value))
        depreciation = documents.depreciation_line_ids.filtered(
            lambda l: l.type != 'create')
        depreciation_move_id = depreciation.mapped('move_id')
        if depreciation_move_id:
            raise ValidationError(_('Depreciation Lines are post already!'))
        depreciation.unlink()
        documents.write({'salvage_value': self.salvage_value})
        return {'type': 'ir.actions.act_window_close'}
