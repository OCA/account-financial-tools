# -*- coding: utf-8 -*-

import logging
from odoo import tools
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    possible_asset_profile_id = fields.Many2one(comodel_name='account.asset.profile',
                                                string='Possible Asset Profile', readonly=True)
    asset_profile_id = fields.Many2one(comodel_name='account.asset.profile', string='Asset Profile', readonly=True)
    tax_profile_id = fields.Many2one(comodel_name='account.bg.asset.profile', string='Tax Asset Profile', readonly=True)
    category_account_id = fields.Many2one(comodel_name='account.account', string='Category account', readonly=True)

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += """,  sub.asset_profile_id as asset_profile_id, sub.tax_profile_id as tax_profile_id, sub.possible_asset_profile_id as possible_asset_profile_id, sub.category_account_id as category_account_id
        """
        return select_str

    def _sub_select(self):
        select_str = super(AccountInvoiceReport, self)._sub_select()
        select_str += """,  ail.asset_profile_id as asset_profile_id, ail.tax_profile_id as tax_profile_id, pc.value_reference as category_account_id, aap.id as possible_asset_profile_id
        """
        return select_str

    def _from(self):
        from_str = super(AccountInvoiceReport, self)._from()
        from_str += """
        LEFT JOIN
            (SELECT company_id, split_part(res_id, ',', 2)::integer as res_id, split_part(value_reference, ',', 2)::integer as value_reference FROM ir_property WHERE name = 'property_stock_valuation_account_id' and split_part(res_id, ',', 1) = 'product.category' and split_part(value_reference, ',', 1) = 'account.account') as pc
                on pc.res_id =  pt.categ_id and pc.company_id = ai.company_id
        LEFT JOIN account_asset_profile as aap
                on aap.account_asset_id = pc.value_reference
        """
        return from_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        inx = group_by_str.find('ail.account_id,')
        return group_by_str[:inx] + ' ail.asset_profile_id, ail.tax_profile_id, aap.id, ' + group_by_str[inx:] + ', pc.value_reference '
