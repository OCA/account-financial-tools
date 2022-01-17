# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetProfile(models.Model):
    _inherit = "account.asset.profile"

    transfer_journal_id = fields.Many2one(
        comodel_name="account.journal",
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        string="Transfer Journal",
        check_company=True,
    )
