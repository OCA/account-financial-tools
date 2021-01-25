# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def _get_product_accounts(self):
        accounts = super(ProductTemplate, self)._get_product_accounts()
        if self._context.get('account_inventory_id'):
            inventory = self.env['stock.inventory'].browse([self._context['account_inventory_id']])
            if inventory.edit_accounts:
                accounts.update({
                    'stock_input': inventory.property_stock_account_input or False,
                    'stock_output': inventory.property_stock_account_output or False,
                    'stock_valuation': inventory.property_stock_valuation_account_id or False,
                })
                #_logger.info("ACCOUNTS %s(%s:%s:%s):%s" % (accounts, inventory.property_stock_account_input.code, inventory.property_stock_account_output.code, inventory.property_stock_valuation_account_id.code, self._context))
        elif self._context.get('account_inventory_line_id'):
            inventory = self.env['stock.inventory.line'].browse(self._context['account_inventory_line_id'])
            if inventory:
                accounts.update({
                    'stock_input': inventory.property_stock_account_input or False,
                    'stock_output': inventory.property_stock_account_output or False,
                    'stock_valuation': inventory.property_stock_valuation_account_id or False,
                })
        return accounts
