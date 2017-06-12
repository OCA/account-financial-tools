# -*- coding: utf-8 -*-
# Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models, tools


class AssetAssetReport(models.Model):
    _name = 'asset.asset.report'
    _description = "Assets Analysis"
    _auto = False

    name = fields.Char(string='Year', size=16, required=False, readonly=True)
    date_start = fields.Date(string='Asset Start Date', readonly=True)
    date_remove = fields.Date(string='Asset Removal Date', readonly=True)
    depreciation_date = fields.Date(string='Depreciation Date', readonly=True)
    asset_id = fields.Many2one(
        comodel_name='account.asset.asset', string='Asset', readonly=True)
    asset_category_id = fields.Many2one(
        comodel_name='account.asset.category', string='Asset category')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', readonly=True)
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('open', 'Running'),
                   ('close', 'Close')],
        string='Status', readonly=True)
    depreciation_value = fields.Float(
        string='Amount of Depreciation Lines', readonly=True)
    move_check = fields.Boolean(string='Posted', readonly=True)
    nbr = fields.Integer(string='# of Depreciation Lines', readonly=True)
    depreciation_base = fields.Float(string='Depreciation Base', readonly=True)
    posted_value = fields.Float(string='Posted Amount', readonly=True)
    unposted_value = fields.Float(string='Unposted Amount', readonly=True)
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'asset_asset_report')
        cr.execute("""
            create or replace view asset_asset_report as (
                select
                    min(dl.id) as id,
                    dl.name as name,
                    dl.line_date as depreciation_date,
                    a.date_start as date_start,
                    a.date_remove as date_remove,
                    a.depreciation_base as depreciation_base,
                    dl.amount as depreciation_value,
                    (CASE WHEN dl.move_check
                      THEN dl.amount
                      ELSE 0
                      END) as posted_value,
                    (CASE WHEN NOT dl.move_check
                      THEN dl.amount
                      ELSE 0
                      END) as unposted_value,
                    dl.asset_id as asset_id,
                    dl.move_check as move_check,
                    a.category_id as asset_category_id,
                    a.partner_id as partner_id,
                    a.state as state,
                    count(dl.*) as nbr,
                    a.company_id as company_id
                from account_asset_depreciation_line dl
                    left join account_asset_asset a on (dl.asset_id=a.id)
                group by
                    dl.amount, dl.asset_id, dl.line_date, dl.name,
                    a.date_start, a.date_remove, dl.move_check, a.state,
                    a.category_id, a.partner_id, a.company_id,
                    a.depreciation_base, a.id, a.salvage_value
        )""")
