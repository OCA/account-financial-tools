# Copyright 2020-23 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_cogs_common_vals(self, line):
        vals = super()._get_cogs_common_vals(line)
        sale_line = line.sale_line_id or line.sale_line_ids
        if len(sale_line) == 1:
            vals["sale_line_id"] = sale_line.id
        return vals


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Sale Order Line",
        ondelete="set null",
        index=True,
        copy=False,
    )

    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        related="sale_line_id.order_id",
        string="Sales Order",
        ondelete="set null",
        store=True,
        index=True,
        copy=False,
    )

    def _copy_data_extend_business_fields(self, values):
        # Same way Odoo standard does for purchase_line_id field
        res = super()._copy_data_extend_business_fields(values)
        values["sale_line_id"] = self.sale_line_id.id
        return res
