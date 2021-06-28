# -*- coding: utf-8 -*-
# Copyright 2015-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api


class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    @api.multi
    def unlink_move(self):
        moves = self.mapped('move_id')
        moves.filtered(lambda x: x.state == 'posted').button_cancel()
        moves.unlink()
        self.write({'move_check': False})
        self.mapped('asset_id').filtered(lambda x: x.state == 'close').write({
            'state': 'open',
        })
        return True
