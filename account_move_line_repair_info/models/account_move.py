# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    repair_order_id = fields.Many2one(
        comodel_name="repair.order",
        string="Repair Order",
        ondelete="set null",
        index=True,
        copy=False,
    )
