# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    check_number = fields.Char(
        string="Check Number",
        compute="_compute_check_number",
        store=True,
        readonly=False,
        copy=False,
        index=True,
    )

    @api.depends("payment_id", "payment_id.check_number")
    def _compute_check_number(self):
        for rec in self:
            rec.check_number = rec.payment_id.check_number or ""
