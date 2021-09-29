# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class AccountAssetActions(models.Model):
    _name = "account.asset.actions"
    _description = "Server actions for Compute Assets"
    _order = "date_end desc, date_action desc"

    date_action = fields.Date(string='Compute Action Date', readonly=True)
    date_end = fields.Date(
        string='Date', required=True,
        default=fields.Date.today,
        help="All depreciation lines prior to this date will be automatically"
             " posted")
    asset_move_ids = fields.Many2many("account.move", string="Account move for this actions")
    note = fields.Text("Result")

