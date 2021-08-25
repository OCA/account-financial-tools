# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetProfile(models.Model):
    _inherit = "account.asset.profile"

    no_depreciation = fields.Boolean(
        string="Non-Depreciation",
        help="Check this if you do not want to compute depreciation.",
    )
