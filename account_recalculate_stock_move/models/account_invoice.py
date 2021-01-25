# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.tools import float_compare
from odoo.addons.account.models import account_invoice as accountinvoice

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    account_move_ids = fields.One2many('account.move', compute="_compute_account_move_ids")
    account_move_line_ids = fields.One2many('account.move.line', compute="_compute_account_move_line_ids")

    #account_ids = fields.Many2one('product.product', related='invoice_line_ids.account_id', string='Account in lines')
    product_id = fields.Many2one('product.product', related='invoice_line_ids.product_id', string='Product_id')

    @api.multi
    def _compute_account_move_ids(self):
        for inv in self:
            inv.account_move_ids = False
            domain = [('invoice_id', '=', inv.id)]
            account_move = self.env['account.move.line'].search(domain)
            for move_line in account_move:
                if move_line.move_id.state == 'posted':
                    inv.account_move_ids |= move_line.move_id
            for line in inv.invoice_line_ids:
                for stock_move_line in line.move_line_ids:
                    for move_line in stock_move_line.move_line_ids:
                        for move in move_line.move_id:
                            inv.account_move_ids |= move.account_move_ids
                for purchase in line.purchase_id:
                    for picking in purchase.picking_ids:
                        for move_line in picking.move_lines:
                            if line.product_id == move_line.product_id and line.quantity == move_line.quantity_done:
                                inv.account_move_ids |= move_line.account_move_ids

    @api.multi
    def _compute_account_move_line_ids(self):
        for inv in self:
            inv.account_move_line_ids = False
            account_move = inv.move_id
            if account_move.state == 'posted':
                inv.account_move_line_ids |= account_move.line_ids
            for line in inv.invoice_line_ids:
                picking_ids = self.env['stock.picking']
                for stock_move_line in line.move_line_ids:
                    for move_line in stock_move_line.move_line_ids:
                        for move in move_line.move_id:
                            for account_move in move.account_move_ids:
                                inv.account_move_line_ids |= account_move.line_ids
                for purchase in line.purchase_id:
                    for picking in purchase.picking_ids:
                        picking_ids |= purchase.picking_ids
                        for move_line in picking.move_lines:
                            if line.purchase_line_id == move_line.purchase_line_id:
                                for account_move in move_line.account_move_ids:
                                    inv.account_move_line_ids |= account_move.line_ids
                landed_cost = self.env['stock.landed.cost'].search([('picking_ids', 'in', picking_ids.ids)])
                if landed_cost:
                    for landed_cost_line in landed_cost:
                        for account_move in landed_cost_line.account_move_id:
                            inv.account_move_line_ids |= account_move.line_ids.filtered(lambda r: r.product_id == line.product_id)

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

    @api.multi
    def action_get_account_move_lines(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_account_moves_all_a')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.account_move_line_ids.ids)]
        return action_data

    def _action_invoice_rebuild_pre(self):
        return

    def _action_invoice_rebuild_post(self):
        return

    @api.multi
    def action_invoice_rebuild(self):
        moves = self.env['account.move']
        for invoice in self:
            if invoice.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
                raise UserError(_("You cannot rebuild an invoice with a negative total amount. You should create a credit note instead."))

            invoice._action_invoice_rebuild_pre()
            #_logger.info("REBUILD %s" % invoice)
            if invoice.move_id:
                moves += invoice.move_id
            if invoice.payment_move_line_ids:
                raise UserError(_('You cannot rebuild an invoice which is partially paid. You need to unreconcile related payment entries first.'))

            # First, set the invoices as cancelled and detach the move ids
            self.write({'move_id': False})
            if moves:
                # second, invalidate the move(s)
                moves.button_cancel()
                # delete the move this invoice was pointing to
                # Note that the corresponding move_lines and move_reconciles
                # will be automatically deleted too
                moves.unlink()
            # refill accounts
            for line in self.invoice_line_ids:
                price_unit = line.price_unit
                line._onchange_product_id()
                line.price_unit = price_unit
            # rebuild taxes
            invoice.compute_taxes()
            invoice.action_move_create()
            invoice._action_invoice_rebuild_post()
