# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
from openerp import api, fields, models


class AssetAssetReport(models.Model):
    _name = "asset.asset.report"
    _description = "Assets Analysis"
    _auto = False

    name = fields.Char('Year', size=16, required=False, readonly=True)
    date_start = fields.Date('Asset Start Date', readonly=True)
    date_remove = fields.Date('Asset Removal Date', readonly=True)
    depreciation_date = fields.Date('Depreciation Date', readonly=True)
    asset_id = fields.Many2one(
        'account.asset', string='Asset', readonly=True)
    asset_category_id = fields.Many2one(
        'account.asset.profile', string='Asset category')
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('open', 'Running'), ('close', 'Close')],
        'Status', readonly=True)
    depreciation_value = fields.Float(
        'Amount of Depreciation Lines', readonly=True)
    move_check = fields.Boolean('Posted', readonly=True)
    nbr = fields.Integer('# of Depreciation Lines', readonly=True)
    asset_value = fields.Float('Asset Value', readonly=True)
    posted_value = fields.Float('Posted Amount', readonly=True)
    unposted_value = fields.Float('Unposted Amount', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)

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
                    a.depreciation_base as asset_value,
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
                    a.profile_id as asset_category_id,
                    a.partner_id as partner_id,
                    a.state as state,
                    count(dl.*) as nbr,
                    a.company_id as company_id
                from account_asset_line dl
                    left join account_asset a on (dl.asset_id=a.id)
                group by
                    dl.amount, dl.asset_id, dl.line_date, dl.name,
                    a.date_start, a.date_remove, dl.move_check, a.state,
                    a.profile_id, a.partner_id, a.company_id,
                    a.depreciation_base, a.id, a.salvage_value
        )""")
