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
        if self._context.get('account_inventory_id'):
            inventory = self.env['stock.inventory'].browse([self._context['account_inventory_id']])
            if inventory.edit_accounts:
                acc_src = inventory.property_stock_account_input.id
                acc_dest = inventory.property_stock_account_output.id
                acc_valuation = inventory.property_stock_valuation_account_id.id
        return journal_id, acc_src, acc_dest, acc_valuation
