# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# Copyright 2017 Luis M. Ontalba - <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    state = fields.Selection(
        selection_add=[('disposed', 'Disposed')],
    )
    disposal_date = fields.Date(string="Disposal date")
    disposal_move_id = fields.Many2one(
        comodel_name='account.move', string="Disposal move")

    def get_disposal_date(self):
        return fields.Date.context_today(self)

    @api.multi
    def set_to_close(self):
        res = super(AccountAssetAsset, self).set_to_close()
        if res:
            self.disposal_move_id = res['res_id']
            self.disposal_move_id.post()
        self.write({
            'state': 'disposed',
            'disposal_date': self.get_disposal_date(),
            })
        return res

    @api.multi
    def action_disposal_undo(self):
        for asset in self.with_context(asset_disposal_undo=True):
            if asset.disposal_move_id:
                asset.disposal_move_id.button_cancel()
                asset.disposal_move_id.unlink()
            if asset.currency_id.is_zero(asset.value_residual):
                asset.state = 'close'
            else:
                asset.state = 'open'
                asset.method_end = asset.category_id.method_end
                asset.method_number = asset.category_id.method_number
                asset.compute_depreciation_board()
        return self.write({
            'disposal_date': False,
            'disposal_move_id': False,
        })


class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    @api.multi
    def post_lines_and_close_asset(self):
        disposed_lines = self.filtered(lambda r: r.asset_id.state ==
                                       'disposed')
        super(AccountAssetDepreciationLine, self).post_lines_and_close_asset()
        disposed_lines.mapped('asset_id').write({'state': 'disposed'})
