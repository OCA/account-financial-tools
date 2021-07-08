# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, tools, _

class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    restatement_asset_id = fields.Many2one(comodel_name='account.asset', string='Restatement Asset', ondelete='restrict')
    restatement_type = fields.Selection(selection=lambda self: self.env['account.asset.restatement.value']._selection_method())

    def _create_accounting_entries(self, move, qty_out):
        res = super(AdjustmentLines, self)._create_accounting_entries(move, qty_out)
        if (self.restatement_asset_id or self.restatement_type) and res[0][2].get('debit') != 0:
            res[0][2].update({
                'restatement_asset_id': self.restatement_asset_id and self.restatement_asset_id.id or False,
                'restatement_type': self.restatement_type and self.restatement_type or self.restatement_asset_id and 'create' or False,
            })
        else:
            res[1][2].update({
                'restatement_asset_id': self.restatement_asset_id and self.restatement_asset_id.id or False,
                'restatement_type': self.restatement_type and self.restatement_type or self.restatement_asset_id and 'create' or False,
            })
        return res
