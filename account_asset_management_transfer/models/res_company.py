# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    asset_transfer_settings = fields.Boolean(string="Asset Transfer", default=False)
    asset_transfer_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        ondelete="restrict",
        copy=False,
    )
