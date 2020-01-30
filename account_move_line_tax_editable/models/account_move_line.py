# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    is_tax_editable = fields.Boolean(
        string="Is tax data editable?", compute="_compute_is_tax_editable"
    )

    @api.depends("move_id.state")
    def _compute_is_tax_editable(self):
        for rec in self:
            rec.is_tax_editable = rec.move_id.state == "draft"
