# Copyright 2013-2022 Akretion France (https://akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    show_warning_vat_required = fields.Boolean(
        compute="_compute_show_warning_vat_required"
    )

    @api.depends("property_account_position_id", "vat")
    @api.depends_context("company")
    def _compute_show_warning_vat_required(self):
        for partner in self:
            show = False
            fp = partner.property_account_position_id
            if fp and fp.vat_required and not partner.vat:
                show = True
            partner.show_warning_vat_required = show
