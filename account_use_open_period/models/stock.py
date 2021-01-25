# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class StockInventory(models.Model):
        _inherit = "stock.inventory"

        @api.multi
        def post_inventory(self):
                if self.company_id.fiscalyear_lock_date and (self.accounting_date == False or self.accounting_date <= self.company_id.fiscalyear_lock_date):
                        self.accounting_date, last_day_date = self.company_id._check_last_lock_date()
                return super(StockInventory, self).post_inventory()


class StockMoveLine(models.Model):
        _inherit = 'stock.move.line'

        def _rebuild_account_move(self):
                move = self.move_id
                if move.company_id.fiscalyear_lock_date and (move.accounting_date == False or move.accounting_date <= move.company_id.fiscalyear_lock_date):
                        move.accounting_date, last_day_date = move.company_id._check_last_lock_date()
                return super(StockMoveLine, self)._rebuild_account_move()
