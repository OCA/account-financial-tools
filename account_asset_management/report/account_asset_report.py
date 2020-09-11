# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Copyright 2020 Tecnativa - Pedro M. Baeza

from odoo import api, fields, models, tools


class AssetAssetReport(models.Model):
    _name = "account.asset.report"
    _description = "Assets Analysis"
    _auto = False

    def _selection_state(self):
        return self.env["account.asset"].fields_get(
            allfields=["state"]
        )["state"]["selection"]

    date = fields.Date(readonly=True)
    depreciation_date = fields.Date(string='Depreciation Date', readonly=True)
    asset_id = fields.Many2one(
        comodel_name="account.asset", string="Asset", readonly=True,
    )
    asset_profile_id = fields.Many2one(
        comodel_name="account.asset.profile",
        string="Asset profile",
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner", readonly=True)
    state = fields.Selection(
        selection=lambda self: self._selection_state(),
        string="Status",
        readonly=True,
    )
    depreciation_value = fields.Float(
        string="Amount of Depreciation Lines", readonly=True
    )
    move_check = fields.Boolean(string="Posted", readonly=True)
    depreciation_count = fields.Integer(
        string="# of Depreciation Lines", readonly=True,
    )
    gross_value = fields.Float(string="Gross Amount", readonly=True)
    posted_value = fields.Float(string="Posted Amount", readonly=True)
    unposted_value = fields.Float(string="Unposted Amount", readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", readonly=True
    )

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'account_asset_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW account_asset_report AS (
                select
                    min(aal.id) as id,
                    aal.line_date as depreciation_date,
                    aa.date_start as date,
                    (CASE WHEN dlmin.id = min(aal.id)
                      THEN aa.purchase_value
                      ELSE 0
                      END) as gross_value,
                    SUM(aal.amount) as depreciation_value,
                    SUM(CASE WHEN aal.move_check
                      THEN aal.amount
                      ELSE 0
                      END) as posted_value,
                    SUM(CASE WHEN NOT aal.move_check
                      THEN aal.amount
                      ELSE 0
                      END) as unposted_value,
                    aal.asset_id as asset_id,
                    aal.move_check as move_check,
                    aa.profile_id as asset_profile_id,
                    aa.partner_id as partner_id,
                    aa.state as state,
                    count(aal.*) as depreciation_count,
                    aa.company_id as company_id
                FROM account_asset_line aal
                    LEFT JOIN account_asset aa on aal.asset_id=aa.id
                    LEFT JOIN (
                        SELECT min(d.id) as id, ac.id as ac_id
                        FROM account_asset_line as d
                            INNER JOIN account_asset as ac
                                ON ac.id = d.asset_id AND d.type = 'depreciate'
                        GROUP BY ac_id
                    ) AS dlmin on dlmin.ac_id = aa.id
                WHERE aal.type = 'depreciate'
                GROUP BY
                    aal.asset_id, aal.line_date, aa.date_start,
                    aal.move_check, aa.state, aa.profile_id,
                    aa.partner_id, aa.company_id, aa.id, dlmin.id
        )""")
