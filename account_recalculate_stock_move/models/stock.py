# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from odoo.addons.stock_account.models.stock import StockMove as stockmove

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

        if move.state == 'done':
            if self._context.get("force_accounting_date"):
                date = self._context['force_accounting_date']
            else:
                date = move.accounting_date or move.date or fields.Date.context_today(self)
            if move.product_id.valuation == 'real_time' and (
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
                price_unit = move.price_unit
                if move.purchase_line_id:
                    price_unit = move._get_price_unit()

                valued_quantity = self.product_uom_id._compute_quantity(self.qty_done, self.product_id.uom_id)
                amount = valued_quantity * abs(price_unit)
                # _logger.info("MOVE STOCK MOVE self._context(%s)::%s\n%s(%s) %s(%s)=%s*%s (purchase_line_id:%s)" %
                #              (self._context, move.remaining_qty, move.product_id.display_name, move._is_dropshipped(), self.qty_done,
                #               price_unit, amount, move.product_id.standard_price, move.purchase_line_id))
                force_asset = allow_asset_removal = allow_asset = False
                if self.asset_id and not self.asset_id.to_sell:
                    force_asset = self.asset_id
                    allow_asset_removal = move._is_out()
                    allow_asset = move._is_in()
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
                or self._is_dropshipped() or self._is_dropshipped_returned()):
            self._rebuild_account_move()
        elif not self.env.context.get("rebuld_try"):
            state = (self.state == 'done') and " " or "*"
            real_time = (self.product_id.valuation == 'real_time') and " " or "*"
            in_out = (self._is_in() or self._is_out() or self._is_in_inventory() or self._is_out_inventory()) and " " or "*"
            raise Warning(_(
                "The operation will not be performed because one of the following conditions may not have been met: \n\n %s1. Status not in \"Done\" \n%s2. The spelling in the product or its category is not in real time.\n%s3. This is not a movement at the entrance or exit of the company.") % (
                              state, real_time, in_out))

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
                date = self.accounting_date or fields.Date.context_today(self)
                price_unit = order.currency_id.with_context(date=date).compute(price_unit, order.company_id.currency_id,
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

# stockmove._get_price_unit = StockMove._get_price_unit
