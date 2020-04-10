# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    account_move_ids = fields.One2many('account.move', compute="_compute_account_move_ids")
    account_move_inv_debit = fields.Float('Debit on invoice', compute="_compute_account_move_inv")
    account_move_inv_credit = fields.Float('Debit on invoice', compute="_compute_account_move_inv")
    account_move_pick_debit = fields.Float('Debit on invoice', compute="_compute_account_move_pick")
    account_move_pick_credit = fields.Float('Debit on invoice', compute="_compute_account_move_pick")

    def _compute_account_move_ids(self):
        for order in self:
            order.account_move_ids = False
            for picking in order.picking_ids:
                if picking.move_lines.mapped("account_move_ids"):
                    for line in picking.move_lines:
                        if not picking.account_move_ids:
                            order.account_move_ids = line.account_move_ids
                        else:
                            order.account_move_ids = order.account_move_ids | line.account_move_ids
            invoice_ids = order.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
            if invoice_ids:
                for inv in invoice_ids:
                    if inv.move_id:
                        move = inv.move_id
                        if not order.account_move_ids:
                            order.account_move_ids = move
                        else:
                            order.account_move_ids |= move

    def _compute_account_move_inv(self):
        for order in self:
            order.account_move_inv_debit = 0.0
            order.account_move_inv_credit = 0.0
            invoice_ids = order.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
            if invoice_ids:
                for inv in invoice_ids:
                    if inv.move_id:
                        order.account_move_inv_debit += sum(x["debit"] for x in inv.move_id.mapped("line_ids"))
                        order.account_move_inv_credit += sum(x["credit"] for x in inv.move_id.mapped("line_ids"))

    def _compute_account_move_pick(self):
        for order in self:
            order.account_move_pick_debit = 0.0
            order.account_move_pick_credit = 0.0
            for picking in order.picking_ids:
                if picking.move_lines.mapped("account_move_ids"):
                    for line in picking.move_lines:
                        order.account_move_pick_debit += sum(x["debit"] for x in line.account_move_ids.mapped("line_ids"))
                        order.account_move_pick_credit += sum(x["credit"] for x in line.account_move_ids.mapped("line_ids"))

    @api.multi
    def action_get_account_moves(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_move_journal_line')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.account_move_ids.ids)]
        action_data['context'] = {'search_default_misc_filter': 0, 'view_no_maturity': True}
        return action_data
