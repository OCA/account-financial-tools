# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from psycopg2 import OperationalError, Error

from odoo import api, fields, models, tools, _
from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.addons.stock.models.stock_quant import StockQuant as stockquant

import logging
_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    move_line_ids = fields.Many2many("stock.move.line", relation="rel_quant_move_line", column1="quant_id", column2="move_line_id", string="Ref stock move line")

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'stock_quant_quantity_update')
        self._cr.execute("""
CREATE VIEW stock_quant_quantity_update AS 
SELECT SUM(ROUND(((ml.qty_done/pu.factor)*ppu.factor)::numeric, length((string_to_array((ppu.rounding::numeric)::text,'.'))[2]))) AS qty_updated, rel.quant_id AS id FROM stock_move_line AS ml
    INNER JOIN product_uom AS pu
        ON pu.id = ml.product_uom_id
    INNER JOIN product_product AS pp
        ON pp.id = ml.product_id
    INNER JOIN product_template AS pt
        ON pt.id = pp.product_tmpl_id
    INNER JOIN product_uom AS ppu
        ON ppu.id = pt.uom_id
    INNER JOIN rel_quant_move_line AS rel
        ON rel.move_line_id = ml.id
    GROUP BY ml.move_id, rel.quant_id;""")

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, in_date=None, line=None):
        """ Increase or decrease `reserved_quantity` of a set of quants for a given set of
        product_id/location_id/lot_id/package_id/owner_id.
        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param datetime in_date: Should only be passed when calls to this method are done in
                                 order to move a quant. When creating a tracked quant, the
                                 current datetime will be used.
        :return: tuple (available_quantity, in_date as a datetime)
        """
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
        rounding = product_id.uom_id.rounding

        incoming_dates = [d for d in quants.mapped('in_date') if d]
        incoming_dates = [fields.Datetime.from_string(incoming_date) for incoming_date in incoming_dates]
        if in_date:
            incoming_dates += [in_date]
        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates:
            in_date = fields.Datetime.to_string(min(incoming_dates))
        else:
            in_date = fields.Datetime.now()

        for quant in quants:
            try:
                with self._cr.savepoint():
                    self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id], log_exceptions=False)
                    if line:
                        quant.write({'move_line_ids': [(4, line.id)]})
                    if self._context.get('force_re_quant'):
                        self._cr.execute("SELECT sum(rel.qty_updated) FROM stock_quant_quantity_update WHERE rel.id = "
                                         "%s GROUP BY rel.id", [quant.id],
                                         log_exceptions=False)
                        results = self.env.cr.fetchall()
                        qty = results[0]
                    else:
                        qty = quant.quantity + quantity
                    res = {
                        'quantity': qty,
                        'in_date': in_date,
                    }
                    quant.write(res)
                    # cleanup empty quants
                    if float_is_zero(quant.quantity, precision_rounding=rounding) and float_is_zero(quant.reserved_quantity, precision_rounding=rounding):
                        query = "DELETE FROM %s WHERE quant_id = %%s" % 'rel_quant_move_line'
                        self._cr.execute(query, (quant.id,))
                        quant.unlink()
                    break
            except OperationalError as e:
                if e.pgcode == '55P03':  # could not obtain the lock
                    continue
                else:
                    raise
        else:
            res = {
                'product_id': product_id.id,
                'location_id': location_id.id,
                'quantity': quantity,
                'lot_id': lot_id and lot_id.id,
                'package_id': package_id and package_id.id,
                'owner_id': owner_id and owner_id.id,
                'in_date': in_date,
                'company_id': location_id and location_id.company_id.id,
            }
            if line:
                res['move_line_ids'] = [(4, line.id)]
            self.create(res)
        return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=False, allow_negative=True), fields.Datetime.from_string(in_date)

stockquant._update_available_quantity = StockQuant._update_available_quantity
