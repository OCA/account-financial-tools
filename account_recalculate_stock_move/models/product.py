# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID
from psycopg2 import OperationalError, Error
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare

import logging
_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = "product.product"

    account_move_line_ids = fields.One2many('account.move.line', inverse_name="product_id", string="Account entries")

    def rebuild_moves(self):
        company = self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        location = warehouse.lot_stock_id
        product = self
        moves = self.env['stock.move'].search([('product_id', '=', self.id)])
        if moves:
            raise UserError(_(
                "You cannot rebuild quantities from pickings moves in product.\n "
                "You need to try from the product template."))

            # quants = self.env['stock.quant'].sudo()._gather(product, location, strict=False)
            # for quant in quants:
            #     try:
            #         with self._cr.savepoint():
            #             self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
            #                              log_exceptions=False)
            #             quant.unlink()
            #             break
            #     except OperationalError as e:
            #         if e.pgcode == '55P03':  # could not obtain the lock
            #             continue
            #         else:
            #             raise
            # moves.force_rebuild_moves()

    @api.multi
    def action_get_account_move_lines(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_account_moves_all_a')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.account_move_line_ids.ids)]
        action_data['context'] = {'search_default_movegroup': 1}
        return action_data


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    account_move_line_ids = fields.One2many('account.move.line', compute="_compute_account_move_line_ids")

    def _compute_account_move_line_ids(self):
        for template in self:
            template.account_move_line_ids = False
            for product in template.product_variant_ids:
                if not template.account_move_line_ids:
                    template.account_move_line_ids = product.account_move_line_ids
                else:
                    template.account_move_line_ids |= product.account_move_line_ids

    def rebuild_moves(self):
        company = self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        location = warehouse.lot_stock_id

        # force remove quant's
        for product in self.product_variant_ids:
            rounding = product.uom_id.rounding
            quants = self.env['stock.quant'].sudo()._gather(product, location, strict=False)

            for quant in quants:
                try:
                    with self._cr.savepoint():
                        self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
                                         log_exceptions=False)
                        quant.write({
                            'quantity': 0,
                            'reserved_quantity': 0,
                        })
                        # cleanup empty quants
                        if float_is_zero(quant.quantity, precision_rounding=rounding) and float_is_zero(
                                quant.reserved_quantity, precision_rounding=rounding):
                            quant.unlink()
                        #break
                except OperationalError as e:
                    if e.pgcode == '55P03':  # could not obtain the lock
                        continue
                    else:
                        raise

            quants = self.env['stock.quant'].sudo()._gather(product, location, strict=False)
            moves = self.env['stock.move'].search([('product_id', '=', product.id), ('state', '=', 'done')])
            if self._uid == SUPERUSER_ID:
                moves = moves.filtered(lambda r: r.company_id == self.env.user.company_id)

            for move in moves.sorted(lambda r: r.date):
                #move.write({"state": 'assigned'})
                #move.move_line_ids.write({"state": 'assigned'})
                acc_moves = False
                for acc_move in move.account_move_ids:
                    if acc_move.state == 'posted':
                        if not acc_moves:
                            acc_moves = acc_move
                        else:
                            acc_moves |= acc_move
                if acc_moves:
                    for acc_move in acc_moves:
                        if acc_move.state == 'draft':
                            acc_move.unlink()
                            continue
                        ret = acc_move.button_cancel()
                        if ret:
                            acc_move.unlink()
                move.move_line_ids.filtered(lambda r: float_compare(r.qty_done, 0, precision_rounding=r.product_uom_id.rounding) > 0)._action_done()
                # _logger.info("MOVE %s" % move.reference)
                if move.picking_id:
                    move.write({'date': move.picking_id.date_done,
                                'accounting_date': move.picking_id.date_done})
                    move.move_line_ids.write({'date': move.picking_id.date_done})
                if move.inventory_id:
                    move.write({'date': move.inventory_id.accounting_date or move.inventory_id.date,
                                'accounting_date': move.inventory_id.accounting_date or move.inventory_id.date})
                    move.move_line_ids.write({'date': move.inventory_id.accounting_date or move.inventory_id.date})
                move.with_context(dict(self._context, force_date=move.date, rebuld_try=True)).rebuild_account_move()

    @api.multi
    def action_get_account_move_lines(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_account_moves_all_a')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.account_move_line_ids.ids)]
        action_data['context'] = {'search_default_movegroup': 1}
        return action_data
