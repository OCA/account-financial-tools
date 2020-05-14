# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    is_initial_balance = fields.Boolean('This is initial balance')

    def _get_accounting_data_for_valuation(self):
        journal_id, acc_src, acc_dest, acc_valuation = super(StockMove, self)._get_accounting_data_for_valuation()
        if self.is_initial_balance:
            opening_move_id = self.company_id.account_opening_move_id
            unaffected_earnings_account = self.company_id.get_unaffected_earnings_account()
            journal_id = opening_move_id.journal_id.id
            acc_src = acc_dest = unaffected_earnings_account.id
            #_logger.info("MOVE %s==>%s:%s:%s:%s" % (opening_move_id, journal_id, acc_src, acc_dest, acc_valuation))
        return journal_id, acc_src, acc_dest, acc_valuation
