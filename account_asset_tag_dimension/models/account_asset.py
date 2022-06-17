# Copyright 2022 Ecosoft Co., Ltd. (https://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountAsset(models.Model):
    _name = "account.asset"
    _inherit = ["analytic.dimension.line", "account.asset"]
    _analytic_tag_field_name = "analytic_tag_ids"
