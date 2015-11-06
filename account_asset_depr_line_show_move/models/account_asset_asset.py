# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api, _


class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    @api.multi
    def open_move(self):
        self.ensure_one()
        return {
            'name': _("Journal Entry"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'nodestroy': True,
        }
