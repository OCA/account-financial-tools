# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    origin_move_id = fields.Many2one('account.move', string="Origin move",
                                     help="Account move for which this move is the origin for transfer")
    has_origin_move_id = fields.Boolean(compute="_compute_has_origin_move_id")
    origin_move_ids = fields.One2many('account.move', "origin_move_id", string="Ref moves",
                                     help="Account move for which this move is the ref for transfer")
    has_origin_move_ids = fields.Boolean(compute="_compute_has_origin_move_ids")

    @api.depends('origin_move_id')
    def _compute_has_origin_move_id(self):
        for move in self:
            move.has_origin_move_id = len(move.origin_move_id.ids) > 0

    @api.depends('origin_move_ids')
    def _compute_has_origin_move_ids(self):
        for move in self:
            move.has_origin_move_ids = len(move.origin_move_ids.ids) > 0

    @api.multi
    def action_get_account_moves(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_move_journal_line')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        if self.origin_move_id:
            action_data['domain'] = [('id', '=', self.origin_move_id.id)]
        else:
            action_data['domain'] = [('id', 'in', self.origin_move_ids.ids)]
        action_data['context'] = {'search_default_misc_filter': 0, 'view_no_maturity': True}
        return action_data
