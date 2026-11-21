# Copyright 2015-2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    cost_center_id = fields.Many2one(
        "account.cost.center",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Default Cost Center",
    )
