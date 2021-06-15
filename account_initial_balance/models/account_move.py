# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    is_initial_balance = fields.Boolean('This is initial balance')

    @api.multi
    def action_see_initial_balance(self):
        for move in self:
            if move.patient_data_ids:
                attachment_view = self.env.ref('account.setup_opening_move_wizard_form')
                return {
                    'name': _('Initial balance'),
                    'res_model': 'account.opening',
                    'type': 'ir.actions.act_window',
                    'view_id': attachment_view.id,
                    'views': [(False, 'tree'), (attachment_view, 'form')],
                    'view_mode': 'tree,form',
                    'view_type': 'form',
                    'context': "{'default_company_id': %s}" % self.env.user.company_id.id,
                    }
        return False

# get from account_move_line_stock_info
# removed
# class AccountMoveLine(models.Model):
#     _inherit = "account.move.line"
# 
#     stock_move_id = fields.Many2one('stock.move', string='Stock Move')
