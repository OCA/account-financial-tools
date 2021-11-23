# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID
from psycopg2 import OperationalError, Error
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp
from odoo.addons.stock_account.models.product import ProductProduct as productproduct

import logging
_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = "product.product"

    account_move_line_ids = fields.One2many('account.move.line', inverse_name="product_id", string="Account entries")
    account_value = fields.Float(
        'Account Value', compute='_compute_stock_value')
    account_qty_at_date = fields.Float(
        'Account Quantity', compute='_compute_stock_value')
    account_standard_price = fields.Float(
        'Account Cost', compute='_compute_stock_value',
        digits=dp.get_precision('Product Price'))
    history_value = fields.Float(
        'History Value', compute='_compute_stock_value',
        digits=dp.get_precision('Product Price'))

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

    @api.multi
    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.remaining_value',
                 'product_tmpl_id.cost_method', 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation',
                 'product_tmpl_id.categ_id.property_valuation')
    def _compute_stock_value(self):
        StockMove = self.env['stock.move']
        to_date = self.env.context.get('to_date')

        real_time_product_ids = [product.id for product in self if product.product_tmpl_id.valuation == 'real_time']
        if real_time_product_ids:
            self.env['account.move.line'].check_access_rights('read')
            fifo_automated_values = {}
            query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                         FROM account_move_line AS aml
                        WHERE aml.product_id IN %%s AND aml.company_id=%%s %s
                     GROUP BY aml.product_id, aml.account_id"""
            params = (tuple(real_time_product_ids), self.env.user.company_id.id)
            if to_date:
                query = query % ('AND aml.date <= %s',)
                params = params + (to_date,)
            else:
                query = query % ('',)
            self.env.cr.execute(query, params=params)

            res = self.env.cr.fetchall()
            for row in res:
                fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        product_values = {product.id: 0 for product in self}
        product_move_ids = {product.id: [] for product in self}

        if to_date:
            domain = [('product_id', 'in', self.ids), ('date', '<=', to_date)] + StockMove._get_all_base_domain()
            value_field_name = 'value'
        else:
            domain = [('product_id', 'in', self.ids)] + StockMove._get_all_base_domain()
            value_field_name = 'remaining_value'

        StockMove.check_access_rights('read')
        query = StockMove._where_calc(domain)
        StockMove._apply_ir_rules(query, 'read')
        from_clause, where_clause, params = query.get_sql()
        query_str = """
            SELECT stock_move.product_id, SUM(COALESCE(stock_move.{}, 0.0)), ARRAY_AGG(stock_move.id)
            FROM {}
            WHERE {}
            GROUP BY stock_move.product_id
        """.format(value_field_name, from_clause, where_clause)
        self.env.cr.execute(query_str, params)
        for product_id, value, move_ids in self.env.cr.fetchall():
            product_values[product_id] = value
            product_move_ids[product_id] = move_ids

        for product in self:
            qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
            price_used = product.standard_price
            if to_date:
                price_used = product.get_history_price(
                    self.env.user.company_id.id,
                    date=to_date,
                )
            product.history_value = price_used * qty_available
            product.account_standard_price = price_used

            if product.cost_method in ['standard', 'average']:
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
                product.account_value = price_used * qty_available
                product.account_qty_at_date = qty_available
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_value = product_values[product.id]
                        product.qty_at_date = qty_available
                        product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
                        product.account_value = product_values[product.id]
                        product.account_qty_at_date = qty_available
                        if qty_available != 0:
                            product.account_standard_price = product_values[product.id]/qty_available
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                        0, 0, [])
                        product.stock_value = value
                        product.qty_at_date = quantity
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
                        product.account_value = value
                        product.account_qty_at_date = quantity
                        if quantity != 0:
                            product.account_standard_price = value/quantity
                else:
                    product.stock_value = product_values[product.id]
                    product.qty_at_date = qty_available
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
                        product.account_value = product_values[product.id]
                        product.account_qty_at_date = qty_available
                        if qty_available != 0:
                            product.account_standard_price = product_values[product.id]/qty_available
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                        0, 0, [])
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
                        product.account_value = value
                        product.account_qty_at_date = quantity
                        if quantity != 0:
                            product.account_standard_price = value/quantity


productproduct._compute_stock_value = Product._compute_stock_value


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

    def _rebuild_moves(self, product, move, date_move):
        return

    def rebuild_moves(self):
        company = self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        location = warehouse.lot_stock_id

        # force remove quant's
        for product in self.product_variant_ids:
            rounding = product.uom_id.rounding
            quants = self.env['stock.quant'].sudo()._gather(product, location, strict=False)
            # _logger.info("QUINTS FOR PRODUCT IN LOCATIONS %s:%s:%s:%s" % (product.default_code, product, location.name, quants))

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

            history = self.env['product.price.history'].search([
                ('company_id', '=', company),
                ('product_id', 'in', self.product_variant_ids.ids)], order='datetime desc,id desc')
            if history:
                history.unlink()
            # quants = self.env['stock.quant'].sudo()._gather(product, location, strict=False)
            # _logger.info("QUINTS FOR PRODUCT IN LOCATIONS %s:%s:%s:%s" % (product.default_code, product, location.name, quants))

            moves = self.env['stock.move'].search([('product_id', '=', product.id), ('state', '=', 'done')])
            if self._uid == SUPERUSER_ID:
                moves = moves.filtered(lambda r: r.company_id == self.env.user.company_id)
            landed_cost = self.env['stock.valuation.adjustment.lines'].search([('move_id', 'in', moves.ids)])
            #try:
            # _logger.info("MOVES %s" % moves)
            date_move = False
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
                move.remaining_value = 0.0
                move.remaining_qty = 0.0
                move.value = 0.0
                correction_value = move._run_valuation(move.qty_done)
                for move_line in move.move_line_ids.filtered(lambda r: float_compare(r.qty_done, 0, precision_rounding=r.product_uom_id.rounding) > 0):
                    move_line._action_done()
                # _logger.info("MOVE %s" % move.reference)
                if move.picking_id:
                    move.write({'date': move.picking_id.date_done,
                                'accounting_date': move.picking_id.date_done})
                    move.move_line_ids.write({'date': move.picking_id.date_done})
                if move.inventory_id:
                    move.write({'date': move.inventory_id.accounting_date or move.inventory_id.date,
                                'accounting_date': move.inventory_id.accounting_date or move.inventory_id.date})
                    move.move_line_ids.write({'date': move.inventory_id.accounting_date or move.inventory_id.date})
                move.with_context(dict(self._context, force_valuation_amount=correction_value, force_date=move.date,
                                       rebuld_try=True)).rebuild_account_move()
                move_landed_cost = landed_cost.filtered(lambda r: r.move_id == move)
                if move_landed_cost:
                    move_landed_cost.former_cost = move.value
                if not date_move:
                    date_move = move.date
                move_landed_cost = landed_cost.filtered(lambda r: date_move > r.cost_id.date <= move.date)
                if move_landed_cost:
                    move_landed_cost.mapped('cost_id').rebuild_account_move()
                self._rebuild_moves(product, move, date_move)
                date_move = move.date


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
