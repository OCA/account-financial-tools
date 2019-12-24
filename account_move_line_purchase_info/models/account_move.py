# Copyright 2019 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    purchase_id = fields.Many2one(
        comodel_name="purchase.order",
        related="purchase_line_id.order_id",
        string="Purchase Order",
        store=True,
        index=True,
    )
