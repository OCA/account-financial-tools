# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # def _rebuild_moves(self, product, move, date_move):
    #     res = super(ProductTemplate, self)._rebuild_moves(product, move, date_move)
    #     if move.workorder_id:
    #         production = move.workorder_id.production_id
    #         if production.date_finished and date_move > production.date_finished <= move.date:
    #             production.rebuild_account_move()
    #     return res

    def _pre_rebuild_moves(self, product, move, date_move):
        if move.production_id:
            production = move.production_id
            production.with_context(dict(self._context, force_accounting_date=production.date_finished)). \
                _cal_price(production.move_raw_ids.filtered(lambda x: x.state == 'done'))
        return True
