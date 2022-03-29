# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class RepairOrder(models.Model):

    _inherit = "repair.order"

    account_move_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="repair_order_id",
        string="Journal Entries",
        required=False,
    )
