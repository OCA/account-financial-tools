# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class Inventory(models.Model):
    _inherit = "stock.inventory"

    edit_accounts = fields.Boolean(string='Edit accounts')
    property_stock_account_input = fields.Many2one(
        'account.account', 'Stock Input Account',
        company_dependent=True, domain=[('deprecated', '=', False)],
        )
    property_stock_account_output = fields.Many2one(
        'account.account', 'Stock Output Account',
        company_dependent=True, domain=[('deprecated', '=', False)],
        )
    property_stock_valuation_account_id = fields.Many2one(
        'account.account', 'Stock Valuation Account',
        company_dependent=True, domain=[('deprecated', '=', False)],
        )

    @api.onchange('edit_accounts')
    def _onchage_edit_accounts(self):
        if not self.edit_accounts:
            self.property_stock_account_input = False
            self.property_stock_account_output = False
            self.property_stock_valuation_account_id = False

    def post_inventory(self):
        if self.edit_accounts:
            self = self.with_context(dict(self._context, account_inventory_id=self.id))
        return super(Inventory, self).post_inventory()

    def rebuild_account_move(self):
        return super(Inventory, self.with_context(dict(self._context, account_inventory_id=self.id))).rebuild_account_move()
