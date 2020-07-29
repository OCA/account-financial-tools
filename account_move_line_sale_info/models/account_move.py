# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Sale Order Line",
        ondelete="set null",
        index=True,
    )

    sale_id = fields.Many2one(
        comodel_name="sale.order",
        related="sale_line_id.order_id",
        string="Sales Order",
        ondelete="set null",
        store=True,
        index=True,
    )
