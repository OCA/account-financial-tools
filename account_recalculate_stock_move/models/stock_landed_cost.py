# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    @api.multi
    def action_get_account_moves(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_move_journal_line')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', '=', self.account_move_id.id)]
        action_data['context'] = {'search_default_misc_filter':0, 'view_no_maturity': True}
        return action_data
