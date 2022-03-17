# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from odoo.addons.stock_account.models.stock import StockMove as stockmove

import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        if reserved_quant:
            for record in self:
                # production_id = record.raw_material_production_id
                if record.raw_material_production_id:
                    production_id = record.raw_material_production_id
                    product = record.product_id
                    product.product_tmpl_id.message_post_with_view('mail.message_origin_link',
                                                                   values={'self': product.product_tmpl_id,
                                                                           'origin': production_id},
                                                                   subtype_id=self.env.ref('mail.mt_note').id)
        return super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
