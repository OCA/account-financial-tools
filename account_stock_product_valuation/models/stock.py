# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def _get_accounting_data_for_valuation(self):
        journal_id, acc_src, acc_dest, acc_valuation = super(StockMove, self)._get_accounting_data_for_valuation()
        for move in self:
            if move.product_id.valuation == 'real_time' and move.product_id.property_stock_valuation_account:
                acc_valuation = move.product_id.property_stock_valuation_account.id
        return journal_id, acc_src, acc_dest, acc_valuation