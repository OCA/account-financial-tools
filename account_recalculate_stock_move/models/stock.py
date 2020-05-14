# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.addons.stock.models.stock_move_line import StockMoveLine as stockmoveline
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero

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

    def _rebuild_account_move(self):
        move = self.move_id
        if move.state == 'done':
            if self._context.get("force_valuation"):
                move._run_valuation(self.qty_done)
            if self._context.get("force_accounting_date"):
                date = self._context['force_accounting_date']
            else:
                date = move.accounting_date or move.date or fields.Date.context_today(self)
            if move.product_id.valuation == 'real_time' and (move._is_in() or move._is_out() or move._is_in_inventory() or move._is_out_inventory()):
                amount = self.qty_done * abs(move.price_unit)
                if amount == 0.0 and self.product_id.standard_price == 0.0:
                    # first try to get PO
                    if move.purchase_line_id:
                        price_unit = move.purchase_line_id.price_unit
                        if price_unit == 0.0:
                            sellers = self.product_id._prepare_sellers(False)
                            price_unit = 0.0
                            for seller in sellers.filtered(lambda s: not s.company_id or s.company_id.id == self.company_id.id):
                                if seller.product_id and seller.product_id != self or seller.product_tmpl_id.id != self.product_tmpl_id.id:
                                    continue
                                price_unit = self.product_id.currency_id.compute(seller.price, seller.currency_id)
                                break
                        self.write({"price_unit": price_unit})
                if move._is_in() or move._is_in_inventory():
                    amount = -amount
                move.with_context(dict(self._context, forced_quantity=self.qty_done, force_valuation_amount=amount, force_period_date=date))._account_entry_move()

    #@api.multi
    #def write(self, vals):
    #    res = super(StockMoveLine, self).write(vals)
    #    if 'product_id' in vals:
    #        for move_line in self:
    #            move = move_line.move_id
    #            if move.company_id.currency_id.is_zero(
    #                    move_line.price_unit) and not move_line.location_id._should_be_valued() and not move_line.location_dest_id._should_be_valued():
    #                move_line.price_unit = move._get_price_unit()
    #    return res

    def unlink(self):
        ml = self
        res = super(StockMoveLine, self).unlink()
        if res:
            query = "DELETE FROM %s WHERE move_line_id IN %%s" % 'rel_quant_move_line'
            self._cr.execute(query, (tuple(ml.ids),))
        return res

    def _action_done(self):
        """ This method is called during a move's `action_done`. It'll actually move a quant from
        the source location to the destination location, and unreserve if needed in the source
        location.

        This method is intended to be called on all the move lines of a move. This method is not
        intended to be called when editing a `done` move (that's what the override of `write` here
        is done.
        """

        # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_to_delete = self.env['stock.move.line']
        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%s" doesn\'t respect the rounding precision \
                                  defined on the unit of measure "%s". Please change the quantity done or the \
                                  rounding precision of your unit of measure.') % (ml.product_id.display_name, ml.product_uom_id.name))

            qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking != 'none':
                    picking_type_id = ml.move_id.picking_type_id
                    if picking_type_id:
                        if picking_type_id.use_create_lots:
                            # If a picking type is linked, we may have to create a production lot on
                            # the fly before assigning it to the move line if the user checked both
                            # `use_create_lots` and `use_existing_lots`.
                            if ml.lot_name and not ml.lot_id:
                                lot = self.env['stock.production.lot'].create(
                                    {'name': ml.lot_name, 'product_id': ml.product_id.id}
                                )
                                ml.write({'lot_id': lot.id})
                        elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                            # If the user disabled both `use_create_lots` and `use_existing_lots`
                            # checkboxes on the picking type, he's allowed to enter tracked
                            # products without a `lot_id`.
                            continue
                    elif ml.move_id.inventory_id:
                        # If an inventory adjustment is linked, the user is allowed to enter
                        # tracked products without a `lot_id`.
                        continue

                    if not ml.lot_id:
                        raise UserError(_('You need to supply a lot/serial number for %s.') % ml.product_id.name)
            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            else:
                ml_to_delete |= ml
        ml_to_delete.unlink()

        # Now, we can actually move the quant.
        done_ml = self.env['stock.move.line']
        for ml in self - ml_to_delete:
            if ml.product_id.type == 'product':
                Quant = self.env['stock.quant']
                rounding = ml.product_uom_id.rounding

                # if this move line is force assigned, unreserve elsewhere if needed
                if not ml.location_id.should_bypass_reservation() and float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) > 0:
                    qty_done_product_uom = ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id, rounding_method='HALF-UP')
                    extra_qty = qty_done_product_uom - ml.product_qty
                    ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, ml_to_ignore=done_ml)
                # unreserve what's been reserved
                if not ml.location_id.should_bypass_reservation() and ml.product_id.type == 'product' and ml.product_qty:
                    try:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    except UserError:
                        Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

                # move what's been actually done
                quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                if available_qty < 0 and ml.lot_id:
                    # see if we can compensate the negative quants with some untracked quants
                    untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if untracked_qty:
                        taken_from_untracked_qty = min(untracked_qty, abs(quantity))
                        Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
                        Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
                Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, line=ml, in_date=in_date)
            done_ml |= ml
        # Reset the reserved quantity as we just moved it to the destination location.
        date = self._context.get('force_date') or fields.Datetime.now()
        if any([x.move_id.accounting_date for x in self]):
            for record in self:
                if record.move_id.accounting_date:
                    date = record.move_id.accounting_date
                    break
        (self - ml_to_delete).with_context(bypass_reservation_update=True).write({
            'product_uom_qty': 0.00,
            'date': date,
        })


class StockMove(models.Model):
    _inherit = "stock.move"

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
                        line._rebuild_account_move()
                except:
                    _logger.info("STOCK MOVE %s unposted" % move.name)
                    pass
            elif not move.account_move_ids and move.state == 'done' and not self.env.context.get("rebuld_try"):
                for line in move.move_line_ids:
                    line._rebuild_account_move()

    def rebuild_account_move(self):
        if not self.account_move_ids and self.state == 'done' and self.product_id.valuation == 'real_time' and (
                self._is_in() or self._is_out() or self._is_in_inventory() or self.move._is_out_inventory()):
            self._rebuild_account_move()
        else:
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
            #_logger.info("CANCEL MOVES %s:%s" % (moves, picking))
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

stockmoveline._action_done = StockMoveLine._action_done
