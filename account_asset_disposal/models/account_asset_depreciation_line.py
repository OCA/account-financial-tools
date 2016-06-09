# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountAssetDepreciationLine(models.Model):
    _inherit = "account.asset.depreciation.line"

    @api.multi
    def create_move(self):
        res = super(AccountAssetDepreciationLine, self).create_move()
        for line in self:
            asset = line.asset_id
            if asset.state == 'close' and not asset.disposal_move_id:
                # Asset is closed and no disposal move created,
                # Create disposal move with date (using this priority):
                # - Depreciation date via context
                # - Last posted deprecition line
                # - Current depreciated line
                # - Today
                last_posted_line = self.search([
                    ('asset_id', '=', asset.id),
                    ('move_id', '!=', False),
                ], order='depreciation_date DESC', limit=1)
                depreciation_date = (
                    self.env.context.get('depreciation_date') or
                    last_posted_line.depreciation_date or
                    line.depreciation_date or
                    fields.Date.context_today(line)
                )
                asset.disposal_move_create(
                    depreciation_date, asset.category_id.loss_account_id)
                asset.write({'disposal_date': depreciation_date})
        return res
