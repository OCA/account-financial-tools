# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_stock_valuation_account = fields.Many2one(
        'account.account', 'Stock Valuation Account',
        company_dependent=True, domain=[('deprecated', '=', False)],
        )

    @api.multi
    def _get_product_accounts(self):
        accounts = super(ProductTemplate, self)._get_product_accounts()
        for product in self:
            if product.valuation == 'real_time' and product.property_stock_valuation_account:
                accounts.update({
                    'stock_valuation': product.property_stock_valuation_account or False,
                })
        return accounts
