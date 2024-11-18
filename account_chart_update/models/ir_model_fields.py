# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    @api.depends_context("account_chart_update")
    def _compute_display_name(self):
        """Return special label when showing fields in chart update wizard."""
        res = super()._compute_display_name()
        if self.env.context.get("account_chart_update"):
            for record in self:
                record.display_name = f"{record.field_description} ({record.name})"
        return res
