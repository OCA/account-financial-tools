# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from odoo.addons.stock_account.models.stock import StockMove as stockmoveprice
from odoo.addons.purchase.models.stock import StockMove as stockmove

import logging

_logger = logging.getLogger(__name__)


class StockLocation(models.Model):
    _inherit = "stock.location"

    def _should_be_inventory_valued(self):
        """ This method returns a boolean reflecting whether the products stored in `self` should
        be considered when valuating the stock of a company.
        """
        self.ensure_one()
        if self.usage == 'inventory':
            return True
        return False


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # quant_ids = fields.Many2many("stock.quant", relation="rel_quant_move_line", column1="move_line_id", column2="quant_id", string="Ref quant")
    has_account_move = fields.Boolean(compute="_compute_has_account_move")
    accounting_date = fields.Date('Force Accounting Date', related='move_id.accounting_date')
    picking_date = fields.Datetime('Picking Date', related='picking_id.scheduled_date')

    @api.depends('account_move_line_ids')
    def _compute_has_account_move(self):
        for move in self:
            move.has_account_move = len(move.account_move_line_ids.ids) > 0

    def _rebuild_account_move(self):
        move = self.move_id
        if not move.price_unit or not move.remaining_value:
            move.product_price_update_before_done()

        if move.state == 'done' and move.product_id.valuation == 'real_time' and (
                move._is_in() or move._is_out() or move._is_in_inventory() or move._is_out_inventory()
                or (not move.company_id.anglo_saxon_accounting and
                    (move._is_dropshipped() or move._is_dropshipped_returned()))):
            # if self._context.get("force_accounting_date"):
            #     product = move.product_id.with_context(
            #         dict(self._context, to_date=self._context['force_accounting_date']))
            #     if product.qty_at_date != 0:
            #         coef = (move._is_out() or move._is_out_inventory()) and -1 or 1
            #         move.price_unit = coef * (product.account_value / product.qty_at_date)
            # if self._context.get('force_production', False):
            #     price_unit = move.value / move.quantity_done
            # else:
            # price_unit = move.price_unit
            # if move.purchase_line_id:
            #     price_unit = move._get_price_unit()
            """ Accounting Valuation Entries """
            if self._context.get("force_accounting_date"):
                date = self._context['force_accounting_date']
            else:
                date = move.accounting_date or move.date or fields.Date.context_today(self)

            # all work in base uom for account move
            valued_quantity = self.product_uom_id._compute_quantity(self.qty_done, self.product_id.uom_id)

            if self._context.get('force_valuation_amount') \
                    and self._context.get('force_valuation_amount', 0.0) != 0.0:
                amount = self._context['force_valuation_amount'] / self.quantity_done * self.qty_done
            else:
                price_unit = move.price_unit
                amount = valued_quantity * abs(price_unit)

            force_asset = allow_asset_removal = allow_asset = False
            if self.asset_id and not self.asset_id.to_sell:
                force_asset = self.asset_id
                allow_asset_removal = self._is_out()
                allow_asset = self._is_in()
            move.with_context(dict(self._context,
                                   forced_quantity=valued_quantity,
                                   force_valuation_amount=amount,
                                   force_period_date=date,
                                   force_asset=force_asset,
                                   allow_asset=allow_asset,
                                   allow_asset_removal=allow_asset_removal))._account_entry_move()

    @api.multi
    def rebuild_account_move(self):
        for record in self:
            record.move_id.with_context(dict(self._context, force_accounting_date=record.date)).rebuild_account_move()

    @api.multi
    def rebuild_moves(self, only_remove=True):
        for record in self:
            record.move_id.with_context(dict(self._context, force_accounting_date=record.date)).rebuild_moves(
                only_remove=False)

    def name_get(self):
        res = []
        for move_line in self:
            move = move_line.move_id
            res.append((move_line.id, '%s%s%s>%s' % (
                move.picking_id.origin and '%s/' % move.picking_id.origin or '',
                move.product_id.code and '%s: ' % move.product_id.code or '',
                move.location_id.name, move.location_dest_id.name)))
        return res


class StockMoveUnitPrice(models.Model):
    _inherit = "stock.move"

    def _get_price_unit(self):
        """ Returns the unit price to store on the quant """
        return (not self.company_id.currency_id.is_zero(
            self.price_unit) and self.price_unit or self.product_id.standard_price) * (
                self.product_id.uom_id.factor / self.product_uom.factor )


stockmoveprice._get_price_unit = StockMoveUnitPrice._get_price_unit


class StockMove(models.Model):
    _inherit = "stock.move"

    only_quantity = fields.Boolean('No amount', help='Do not use amount for accounting entries')
    has_account_move = fields.Boolean(compute="_compute_has_account_move")
    accounting_date = fields.Date('Force Accounting Date',
                                  help="Choose the accounting date at which you want to value the stock "
                                       "moves created by the inventory instead of the default one (the "
                                       "inventory end date)")

    @api.depends('account_move_ids')
    def _compute_has_account_move(self):
        for move in self:
            move.has_account_move = len(move.account_move_ids.ids) > 0

    def action_cancel(self):
        if any(move.quantity_done == 0.0 and move.state == 'done' and not move.picking_id for move in self):
            for move in self:
                move.state = 'draft'
            return self._action_cancel()

    @api.multi
    def product_price_update_before_done(self, forced_qty=None):
        tmpl_dict = defaultdict(lambda: 0.0)
        # adapt standard price on incomming moves if the product cost_method is 'average'
        std_price_update = {}
        for move in self.filtered(lambda move: move._is_in() and move.product_id.cost_method == 'average'):
            product_tot_qty_available = move.product_id.qty_available + tmpl_dict[move.product_id.id]
            rounding = move.product_id.uom_id.rounding

            qty_done = move.product_uom._compute_quantity(move.quantity_done, move.product_id.uom_id)
            qty = forced_qty or qty_done
            # If the current stock is negative, we should not average it with the incoming one
            if float_is_zero(product_tot_qty_available, precision_rounding=rounding) or product_tot_qty_available < 0:
                new_std_price = move._get_price_unit()
            elif float_is_zero(product_tot_qty_available + move.product_qty, precision_rounding=rounding) or \
                    float_is_zero(product_tot_qty_available + qty, precision_rounding=rounding):
                new_std_price = move._get_price_unit()
            else:
                # Get the standard price
                amount_unit = std_price_update.get((move.company_id.id, move.product_id.id)) or move.product_id.standard_price * move.product_uom.factor / move.product_id.uom_id.factor
                new_std_price = ((amount_unit * product_tot_qty_available) + (move._get_price_unit() * qty)) / (product_tot_qty_available + qty)

            tmpl_dict[move.product_id.id] += qty_done
            # Write the standard price, as SUPERUSER_ID because a warehouse manager may not have the right to write on products
            move.product_id.with_context(force_company=move.company_id.id).sudo().write({'standard_price': new_std_price})
            std_price_update[move.company_id.id, move.product_id.id] = new_std_price

    @api.model
    def _run_fifo(self, move, quantity=None):
        """ Value `move` according to the FIFO rule, meaning we consume the
        oldest receipt first. Candidates receipts are marked consumed or free
        thanks to their `remaining_qty` and `remaining_value` fields.
        By definition, `move` should be an outgoing stock move.
        :param quantity: quantity to value instead of `move.product_qty`
        :returns: valued amount in absolute
        """
        move.ensure_one()

        # Deal with possible move lines that do not impact the valuation.
        valued_move_lines = move.move_line_ids.filtered(lambda
                                                            ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
        valued_quantity = 0
        for valued_move_line in valued_move_lines:
            valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                 move.product_id.uom_id)

        # Find back incoming stock moves (called candidates here) to value this move.
        qty_to_take_on_candidates = quantity or valued_quantity
        candidates = move.product_id._get_fifo_candidates_in_move()
        new_standard_price = 0
        tmp_value = 0  # to accumulate the value taken on the candidates
        for candidate in candidates:
            new_standard_price = candidate.price_unit
            if candidate.remaining_qty <= qty_to_take_on_candidates:
                qty_taken_on_candidate = candidate.remaining_qty
            else:
                qty_taken_on_candidate = qty_to_take_on_candidates

            # As applying a landed cost do not update the unit price, naivelly doing
            # something like qty_taken_on_candidate * candidate.price_unit won't make
            # the additional value brought by the landed cost go away.
            candidate_price_unit = candidate.remaining_value / candidate.remaining_qty
            value_taken_on_candidate = qty_taken_on_candidate * candidate_price_unit
            candidate_vals = {
                'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                'remaining_value': candidate.remaining_value - value_taken_on_candidate,
            }
            candidate.write(candidate_vals)

            qty_to_take_on_candidates -= qty_taken_on_candidate
            tmp_value += value_taken_on_candidate
            if qty_to_take_on_candidates == 0:
                break

        # Update the standard price with the price of the last used candidate, if any.
        if new_standard_price and move.product_id.cost_method == 'fifo':
            move.product_id.sudo().with_context(force_company=move.company_id.id) \
                .standard_price = new_standard_price * move.product_uom.factor / move.product_id.uom_id.factor

        # If there's still quantity to value but we're out of candidates, we fall in the
        # negative stock use case. We chose to value the out move at the price of the
        # last out and a correction entry will be made once `_fifo_vacuum` is called.
        if qty_to_take_on_candidates == 0:
            move.write({
                'value': -tmp_value if not quantity else move.value or -tmp_value,
                # outgoing move are valued negatively
                'price_unit': -tmp_value / (move.product_qty or quantity),
            })
        elif qty_to_take_on_candidates > 0:
            last_fifo_price = new_standard_price \
                              or move.product_id.standard_price * move.product_id.uom_id.factor / move.product_uom.factor
            negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
            tmp_value += abs(negative_stock_value)
            vals = {
                'remaining_qty': move.remaining_qty + -qty_to_take_on_candidates,
                'remaining_value': move.remaining_value + negative_stock_value,
                'value': -tmp_value,
                'price_unit': -1 * last_fifo_price,
            }
            move.write(vals)
        return tmp_value

    @api.multi
    def _rebuild_account_move(self):
        for move in self:
            if not move.account_move_ids and move.state == 'done' and self.env.context.get("rebuld_try"):
                try:
                    for line in move.move_line_ids:
                        # _logger.info("STOCK MOVE LINE %s" % line)
                        line._rebuild_account_move()
                except UserError:
                    _logger.info("STOCK MOVE %s unposted" % move.name)
                    pass
            elif not move.account_move_ids and move.state == 'done' and not self.env.context.get("rebuld_try"):
                for line in move.move_line_ids:
                    line._rebuild_account_move()

    def rebuild_account_move(self):
        if not self.account_move_ids and self.state == 'done' and self.product_id.valuation == 'real_time' and (
                self._is_in() or self._is_out() or self._is_in_inventory() or self._is_out_inventory()
                or self._is_dropshipped() or self._is_dropshipped_returned()) and self.quantity_done != 0.0:
            self._rebuild_account_move()
        elif not self.env.context.get("rebuld_try"):
            state = (self.state == 'done') and "  " or "* "
            real_time = (self.product_id.valuation == 'real_time') and "  " or "* "
            in_out = (
                             self._is_in() or self._is_out() or self._is_in_inventory() or self._is_out_inventory()) and "  " or "* "
            raise Warning(_(
                "The operation will not be performed because one of the following conditions may not have been met: \n\n"
                "%s1. Status not in \"Done\" \n"
                "%s2. The spelling in the product or its category is not in real time.\n"
                "%s3. This is not a movement at the entrance or exit of the company.\n"
                "%s3.1. This is income.\n"
                "%s3.2. This is outgoing.\n"
                "%s4. Has accounting moves.\n"
                " 4.1. Account moves: %s") % (state, real_time, in_out,
                                              self._is_in() and '* ' or '  ',
                                              self._is_out() and '* ' or '  ',
                                              self.account_move_ids and '* ' or '  ',
                                              ' '.join([x.display_name for x in self.account_move_ids])))

    @api.multi
    def rebuild_moves(self, only_remove=True):
        for move in self.sorted(lambda r: r.date and r.id):
            moves = False
            for acc_move in move.account_move_ids:
                if acc_move.state == 'posted':
                    if not moves:
                        moves = acc_move
                    else:
                        moves |= acc_move
            # _logger.info("CANCEL MOVES %s:%s" % (moves, picking))
            if moves:
                for acc_move in moves:
                    if acc_move.state == 'draft':
                        acc_move.unlink()
                        continue
                    ret = acc_move.button_cancel()
                    if ret:
                        acc_move.unlink()
            if not only_remove:
                date = move.accounting_date or move.date
                move.with_context(dict(self._context, force_date=date)).rebuild_account_move()

    @api.multi
    def force_rebuild_moves(self, only_remove=True):
        for move in self.sorted(lambda r: r.date and r.id):
            moves = False
            for acc_move in move.account_move_ids:
                if acc_move.state == 'posted':
                    if not moves:
                        moves = acc_move
                    else:
                        moves |= acc_move
            # _logger.info("CANCEL MOVES %s:%s" % (moves, picking))
            if moves:
                for acc_move in moves:
                    if acc_move.state == 'draft':
                        acc_move.unlink()
                        continue
                    ret = acc_move.button_cancel()
                    if ret:
                        acc_move.unlink()
            if not only_remove:
                date = move.accounting_date or move.date
                move.with_context(dict(self._context, force_date=date))._action_done()

    def write(self, vals):
        if (vals.get('state', '') == 'done' and vals.get('date')):
            vals['accounting_date'] = vals['date']
        return super(StockMove, self).write(vals)

    def _is_in_inventory(self):
        """ Check if the move should be considered as inventory adjustments so that the cost method
        will be able to apply the correct logic.
        :return: True if the move is inventory adjustments else False
        """
        for move_line in self.move_line_ids.filtered(lambda ml: not ml.owner_id):
            if not move_line.location_id._should_be_inventory_valued() and move_line.location_dest_id._should_be_inventory_valued():
                return True
        return False

    def _is_out_inventory(self):
        """ Check if the move should be considered as inventory adjustments so that the cost method
        will be able to apply the correct logic.
        :return: True if the move is inventory adjustments else False
        """
        for move_line in self.move_line_ids.filtered(lambda ml: not ml.owner_id):
            if move_line.location_id._should_be_inventory_valued() and not move_line.location_dest_id._should_be_inventory_valued():
                return True
        return False

    @api.multi
    def _get_price_unit(self):
        """ Returns the unit price for the move"""
        self.ensure_one()
        if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.price_unit
            inv_line = self.env['account.invoice.line'].search([('purchase_line_id', '=', line.id)])
            if inv_line:
                self.accounting_date = inv_line[0].invoice_id.date_invoice
            if line.taxes_id:
                price_unit = \
                    line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id,
                                                                        quantity=1.0)['total_excluded']
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                # DO NOT FORWARD-PORT! ONLY FOR V11!!!
                # The date must be today, and not the date of the move since the move move is still
                # in assigned state. However, the move date is the scheduled date until move is
                # done, then date of actual move processing. See:
                # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
                # This is problem when receive goods need be possible to choice date for currency rate
                invoice_line_id = self.env['account.invoice.line']. \
                    search([('purchase_line_id', '=', self.purchase_line_id.id)])
                if len(invoice_line_id) > 1:
                    invoice_line_id = invoice_line_id[-1]
                if invoice_line_id:
                    invoice_id = invoice_line_id.invoice_id
                    date = invoice_id.date or invoice_id.date_invoice
                    price_unit = invoice_id.currency_id.with_context(date=date).compute(invoice_line_id.price_unit,
                                                                                        invoice_id.company_id.currency_id,
                                                                                        round=False)
                    if invoice_line_id.uom_id.id != invoice_line_id.product_id.uom_id.id:
                        price_unit *= invoice_line_id.uom_id.factor / invoice_line_id.product_id.uom_id.factor

                else:
                    date = self.accounting_date or fields.Date.context_today(self)
                    price_unit = order.currency_id.with_context(date=date).compute(price_unit,
                                                                                   order.company_id.currency_id,
                                                                                   round=False)

            return price_unit
        return super(StockMove, self)._get_price_unit()

    @api.model
    def _get_in_base_domain(self, company_id=False):
        domain = super(StockMove, self)._get_in_base_domain(company_id=company_id)
        if self._context.get('force_valuation_date'):
            domain += [('date', '<=', self._context['force_valuation_date'])]
        return domain

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        if reserved_quant:
            for record in self:
                # production_id = record.raw_material_production_id
                if record.picking_id:
                    picking_id = record.picking_id
                    product = record.product_id
                    product.product_tmpl_id.message_post_with_view('mail.message_origin_link',
                                                                   values={'self': product.product_tmpl_id,
                                                                           'origin': picking_id},
                                                                   subtype_id=self.env.ref('mail.mt_note').id)
        return super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)


stockmove._get_price_unit = StockMove._get_price_unit
stockmove.product_price_update_before_done = StockMove.product_price_update_before_done
stockmove._run_fifo = StockMove._run_fifo
