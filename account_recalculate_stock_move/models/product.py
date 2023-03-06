# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import uuid

from odoo import SUPERUSER_ID
from psycopg2 import OperationalError, Error
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.addons import decimal_precision as dp
from odoo.addons.stock_account.models.product import ProductProduct as productproduct
from odoo.addons.queue_job.job import job
# from odoo.tools.misc import profile

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

    def clear_reservation_single(self, moves_reservation, location_id, lot_id=None, package_id=None, owner_id=None):
        taken_quantity = False
        for product in self:
            rounding = product.uom_id.rounding
            quants = self.env['stock.quant'].sudo()._gather(product, location_id, lot_id=lot_id,
                                                            package_id=package_id, owner_id=owner_id, strict=True)
            for quant in quants:
                try:
                    with self._cr.savepoint():
                        self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
                                         log_exceptions=False)
                        quant.write({
                            'reserved_quantity': 0,
                        })
                        # cleanup empty quants
                        if float_is_zero(quant.quantity, precision_rounding=rounding) and float_is_zero(
                                quant.reserved_quantity, precision_rounding=rounding):
                            quant.unlink()
                        # break
                except OperationalError as e:
                    if e.pgcode == '55P03':  # could not obtain the lock
                        continue
                    else:
                        raise

            for move in moves_reservation.sorted(lambda r: r.date):
                for line in move.move_line_ids:
                    taken_quantity = line.product_qty
                    try:
                        if not float_is_zero(taken_quantity, precision_rounding=line.product_id.uom_id.rounding):
                            _logger.info('Quant update reservation %s for %s from %s' %
                                         (taken_quantity, line.product_id.display_name, line.move_id.name))
                            quants = self.env['stock.quant']._update_reserved_quantity(
                                line.product_id, move.location_id, taken_quantity, lot_id=line.lot_id,
                                package_id=line.package_id, owner_id=line.owner_id, strict=True
                            )
                            available_quantity = sum(quants.mapped('quantity')) - sum(
                                quants.mapped('reserved_quantity'))
                            taken_quantity = taken_quantity <= available_quantity and taken_quantity or available_quantity
                    except UserError:
                        _logger.info("Exception %s from %s" % (move.product_id.display_name, line.move_id.name))
                        taken_quantity = 0
        return taken_quantity

    def clear_reservation(self):
        company = self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        # location = warehouse.lot_stock_id
        # product = self
        moves = self.env['stock.move'].search([('product_id', '=', self.id)])
        if moves:
            raise UserError(_(
                "You cannot rebuild quantities from pickings moves in product.\n "
                "You need to try from the product template."))

    def rebuild_moves(self):
        company = self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        # location = warehouse.lot_stock_id
        # product = self
        moves = self.env['stock.move'].search([('product_id', '=', self.id)])
        if moves:
            raise UserError(_(
                "You cannot rebuild quantities from pickings moves in product.\n "
                "You need to try from the product template."))

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
        # where_clause += ' AND '
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
            if product.cost_method in ['standard', 'average']:
                qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
                price_used = product.standard_price
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id,
                        date=to_date,
                    )
                product.history_value = price_used * qty_available
                product.account_standard_price = price_used

                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
                product.account_value = price_used * qty_available
                product.account_qty_at_date = qty_available
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_value = product_values[product.id]
                        qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
                        product.qty_at_date = qty_available
                        product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
                        product.account_value = product_values[product.id]
                        product.account_qty_at_date = qty_available
                        if qty_available != 0:
                            product.account_standard_price = product_values[product.id] / qty_available
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
                            product.account_standard_price = value / quantity
                else:
                    qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
                    product.stock_value = product_values[product.id]
                    product.qty_at_date = qty_available
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_fifo_manual_move_ids = StockMove.browse(product_move_ids[product.id])
                        product.account_value = product_values[product.id]
                        product.account_qty_at_date = qty_available
                        if qty_available != 0:
                            product.account_standard_price = product_values[product.id] / qty_available
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                            0, 0, [])
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
                        product.account_value = value
                        product.account_qty_at_date = quantity
                        if quantity != 0:
                            product.account_standard_price = value / quantity


productproduct._compute_stock_value = Product._compute_stock_value


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    account_move_line_ids = fields.One2many('account.move.line', compute="_compute_account_move_line_ids")

    # only_quants = fields.Boolean('Only quantity rebuild')

    def _compute_account_move_line_ids(self):
        for template in self:
            template.account_move_line_ids = False
            for product in template.product_variant_ids:
                if not template.account_move_line_ids:
                    template.account_move_line_ids = product.account_move_line_ids
                else:
                    template.account_move_line_ids |= product.account_move_line_ids

    def clear_reservation_full(self):
        company = self.env.user.company_id.id
        for product in self.product_variant_ids:
            moves = self.env['stock.move'].search([('product_id', '=', product.id),
                                                   ('state', 'in', ('assigned', 'partially_available', 'confirmed'))])
            if self._uid == SUPERUSER_ID:
                moves = moves.filtered(lambda r: r.company_id == self.env.user.company_id)

            # first clear all quantity in table for save
            for warehouse in self.env['stock.warehouse'].search([('company_id', '=', company)]):
                # get for main warehouse location
                location = warehouse.lot_stock_id
                quants = self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for reception warehouse location
                location = warehouse.wh_input_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for quality control location
                location = warehouse.wh_qc_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for delivery warehouse location
                location = warehouse.wh_output_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for packaging location in warehouse
                location = warehouse.wh_pack_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)

                for quant in quants:
                    try:
                        with self._cr.savepoint():
                            self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
                                             log_exceptions=False)
                            quant.write({
                                'reserved_quantity': 0,
                            })
                    except OperationalError as e:
                        if e.pgcode == '55P03':  # could not obtain the lock
                            continue
                        else:
                            raise
            if moves:
                # _logger.info("UPDATE stock_move_line SET product_uom_qty=0.0, product_qty=0.0, ordered_qty=0.0 WHERE id IN %s" % (tuple(moves.mapped('move_line_ids').ids),))
                self._cr.execute("UPDATE stock_move_line SET product_uom_qty=0.0, product_qty=0.0 WHERE id IN %s",
                                 (tuple(moves.mapped('move_line_ids').ids),), log_exceptions=False)
                for move in moves:
                    move._do_unreserve()

    @api.multi
    @job
    def server_clear_reservation_action(self):
        for product in self:
            product.clear_reservation()

    def clear_reservation(self):
        company = self.env.user.company_id.id
        for product in self.product_variant_ids:
            # moves = self.env['stock.move'].search([('product_id', '=', product.id), ('state', '=', 'done')])
            # if self._uid == SUPERUSER_ID:
            #     moves = moves.filtered(lambda r: r.company_id == self.env.user.company_id)
            # if sum([x.product_uom_qty for x in moves.mapped('move_line_ids')]) > 0.0:
            #     raise UserError(_('Before to start recalculation first unreserved all quantity for this product'))

            # rounding = product.uom_id.rounding
            # first clear all quantity in table for save
            for warehouse in self.env['stock.warehouse'].search([('company_id', '=', company)]):
                # get for main warehouse location
                location = warehouse.lot_stock_id
                quants = self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for reception warehouse location
                location = warehouse.wh_input_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for quality control location
                location = warehouse.wh_qc_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for delivery warehouse location
                location = warehouse.wh_output_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for packaging location in warehouse
                location = warehouse.wh_pack_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)

                for quant in quants:
                    try:
                        with self._cr.savepoint():
                            self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id],
                                             log_exceptions=False)
                            quant.write({
                                'reserved_quantity': 0,
                            })
                    except OperationalError as e:
                        if e.pgcode == '55P03':  # could not obtain the lock
                            continue
                        else:
                            raise

            # for move in moves.sorted(lambda r: r.date):
            #     if move.quantity_done == 0:
            #         continue
            #
            #     for move_line in move.move_line_ids.filtered(
            #             lambda r: float_compare(r.qty_done, 0, precision_rounding=r.product_uom_id.rounding) > 0):
            #         move_line._action_done()

            # reservations

            moves_reservation = self.env['stock.move'].search(
                [('product_id', '=', product.id), ('state', 'in', ('assigned', 'partially_available', 'confirmed'))])
            if self._uid == SUPERUSER_ID:
                moves_reservation = moves_reservation.filtered(lambda r: r.company_id == self.env.user.company_id)
            # moves_reservation_try = self.env['stock.move.line']
            for move in moves_reservation.sorted(lambda r: r.date):
                for line in move.move_line_ids:
                    product_qty = line.product_uom_id._compute_quantity(line.ordered_qty,
                                                                        line.product_id.uom_id,
                                                                        rounding_method='HALF-UP')
                    if not float_is_zero(line.ordered_qty, precision_rounding=line.product_uom_id.rounding) \
                            and (float_is_zero(line.product_qty,
                                               precision_rounding=line.product_id.uom_id.rounding)
                                 or float_is_zero(line.product_uom_qty,
                                                  precision_rounding=line.product_uom_id.rounding)):
                        self._cr.execute(
                            "UPDATE stock_move_line SET product_uom_qty = %s, product_qty = %s "
                            "WHERE id = %s", (line.ordered_qty, product_qty, line.id,), log_exceptions=False)
                        # _logger.info("Prepare for update %s(%s=%s) for %s from %s" %
                        #              (line.product_qty,
                        #               line.ordered_qty,
                        #               line.product_uom_qty,
                        #               line.product_id.display_name,
                        #               line.move_id.name))
                    if move.location_id.should_bypass_reservation() or move.product_id.type == 'consu':
                        continue
                    if move.procure_method == 'make_to_order':
                        continue
                    taken_quantity = product_qty
                    # _logger.info("Before update %s(%s) for %s from %s" %
                    #              (taken_quantity, line.ordered_qty, line.product_id.display_name, line.move_id.name))
                    if not float_is_zero(taken_quantity, precision_rounding=line.product_id.uom_id.rounding):
                        try:
                            _logger.info('Quant update reservation %s(%s) for %s from %s' %
                                         (taken_quantity, line.ordered_qty, line.product_id.display_name,
                                          line.move_id.name))
                            quants = self.env['stock.quant']._update_reserved_quantity(
                                line.product_id, line.location_id, taken_quantity, lot_id=line.lot_id,
                                package_id=line.package_id, owner_id=line.owner_id, strict=True
                            )
                        except UserError:
                            _logger.info("Exception %s from %s" % (move.product_id.display_name, line.move_id.name))
                            # moves_reservation_try |= line
                            self._cr.execute(
                                "UPDATE stock_move_line SET product_uom_qty=0.0, product_qty=0.0 WHERE id = %s",
                                (line.id,), log_exceptions=False)
                            taken_quantity = 0
            # for line in moves_reservation_try:
            #     taken_quantity = line.product_qty
            #     try:
            #         if not float_is_zero(taken_quantity, precision_rounding=line.product_id.uom_id.rounding):
            #             _logger.info('Quant update reservation second try %s for %s from %s' %
            #                          (taken_quantity, line.product_id.display_name, line.move_id.name))
            #             quants = self.env['stock.quant']._update_reserved_quantity(
            #                 line.product_id, line.location_id, taken_quantity, lot_id=line.lot_id,
            #                 package_id=line.package_id, owner_id=line.owner_id, strict=True
            #             )
            #     except UserError:
            #         _logger.info("Final exception %s from %s" % (line.product_id.display_name, line.move_id.name))

    # @profile('/tmp/prof.profile')
    @api.multi
    @job
    def server_rebuild_action(self):
        for product in self:
            product.rebuild_moves()

    def _pre_rebuild_moves(self, product, move, date_move):
        return

    def _post_rebuild_moves(self, product, move, date_move):
        return

    def rebuild_moves(self):
        company = self.env.user.company_id.id
        for product in self.product_variant_ids:
            moves = self.env['stock.move'].search([('product_id', '=', product.id), ('state', '=', 'done')])
            if self._uid == SUPERUSER_ID:
                moves = moves.filtered(lambda r: r.company_id == self.env.user.company_id)
            # if sum([x.product_uom_qty for x in moves.mapped('move_line_ids')]) > 0.0:
            #     raise UserError(_('Before to start recalculation first unreserved all quantity for this product'))

            rounding = product.uom_id.rounding
            # first clear all quantity in table for save
            for warehouse in self.env['stock.warehouse'].search([('company_id', '=', company)]):
                # get for main warehouse location
                location = warehouse.lot_stock_id
                quants = self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for reception warehouse location
                location = warehouse.wh_input_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for quality control location
                location = warehouse.wh_qc_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for delivery warehouse location
                location = warehouse.wh_output_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)
                # get for packaging location in warehouse
                location = warehouse.wh_pack_stock_loc_id
                quants |= self.env['stock.quant'].sudo()._gather(product, location, strict=False)

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
                            # break
                    except OperationalError as e:
                        if e.pgcode == '55P03':  # could not obtain the lock
                            continue
                        else:
                            raise
            # second clear all history for product with average or standard price method for cost
            history = self.env['product.price.history'].search([
                ('company_id', '=', company),
                ('product_id', 'in', self.product_variant_ids.ids)], order='datetime desc,id desc')
            if history:
                history.unlink()

            # collect all landed cost for recalculate
            landed_cost = self.env['stock.valuation.adjustment.lines'].search([('move_id', 'in', moves.ids)])
            move_landed_cost = {}
            # landed_move_cost = {}
            if landed_cost:
                landed_cost = landed_cost.sorted(lambda r: r.move_id.date)
            for line_landed in landed_cost:
                move_landed_cost[line_landed.move_id] = line_landed.cost_id

            # first to remove all account moves
            acc_moves_for_remove = self.env['account.move']
            acc_move_acc = self.env['account.move']
            landed_cost_cost_id = landed_cost.mapped('cost_id')
            for landed_line in landed_cost_cost_id:
                for landed_line_acc in landed_line.account_move_line_ids. \
                        filtered(lambda r: r.stock_move_id.id in moves.ids):
                    acc_move_acc |= landed_line_acc.move_id
            acc_move_acc |= moves.mapped('account_move_ids')
            for acc_move in acc_move_acc:
                if acc_move.state == 'posted':
                    acc_moves_for_remove |= acc_move
            if acc_moves_for_remove:
                for acc_move in acc_moves_for_remove:
                    if acc_move.state == 'draft':
                        acc_move.unlink()
                        continue
                    ret = acc_move.button_cancel()
                    if ret:
                        acc_move.unlink()
            for move in moves.sorted(lambda r: r.date):
                if move.quantity_done == 0:
                    continue
                move.write({
                    'landed_cost_value': 0.0,
                    'remaining_value': 0.0,
                    'remaining_qty': 0.0,
                    'value': 0.0,
                    'price_unit': 0.0,
                })
                # move.landed_cost_value = 0.0
                # move.remaining_value = 0.0
                # move.remaining_qty = 0.0
                # move.value = 0.0
                # move.price_unit = 0.0

            # start rebuild all stock moves and account moves
            date_move = False
            for move in moves.sorted(lambda r: r.date):
                if move.quantity_done == 0:
                    continue
                if move.inventory_id:
                    prod_inventory = move.inventory_id.line_ids.filtered(lambda r: r.product_id == move.product_id)
                    if prod_inventory and prod_inventory[0].price_unit != 0:
                        move.price_unit = prod_inventory[0].price_unit

                self._pre_rebuild_moves(product, move, date_move)

                correction_value = move._run_valuation(move.quantity_done)
                for move_line in move.move_line_ids.filtered(
                        lambda r: float_compare(r.qty_done, 0, precision_rounding=r.product_uom_id.rounding) > 0):
                    move_line._action_done()

                # now to regenerate account moves
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
                                       rebuld_try=True, force_re_calculate=True)).rebuild_account_move()
                current_landed_cost = move_landed_cost.get(move, False)
                # _logger.info("CURRENT LANDED COST %s" % current_landed_cost)
                if current_landed_cost:
                    current_landed_cost.rebuild_account_move_lines(move)
                self._post_rebuild_moves(product, move, date_move)

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
