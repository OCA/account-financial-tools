# Copyright 2019 ForgeFlow S.L.
#   (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Set related None, to make it compute and avoid base related to purchase_line_id
    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        related=None,
        store=True,
        index=True,
        compute="_compute_purchase_id",
    )

    oca_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="OCA Purchase Line",
        store=True,
        index=True,
        compute="_compute_oca_purchase_line_id",
    )

    @api.depends("purchase_line_id")
    def _compute_oca_purchase_line_id(self):
        for rec in self:
            if rec.purchase_line_id:
                rec.oca_purchase_line_id = rec.purchase_line_id

    @api.depends("purchase_line_id", "oca_purchase_line_id")
    def _compute_purchase_id(self):
        for rec in self:
            rec.purchase_order_id = (
                rec.purchase_line_id.order_id.id or rec.oca_purchase_line_id.order_id.id
            )
