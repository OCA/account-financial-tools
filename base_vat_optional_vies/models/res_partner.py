# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2017 Tecnativa - David Vidal
# Copyright 2019 FactorLibre - Rodrigo Bonilla
# Copyright 2022 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    vies_passed = fields.Boolean(string="VIES validation", readonly=True)

    @api.model
    def simple_vat_check(self, country_code, vat_number):
        res = super(ResPartner, self).simple_vat_check(
            country_code,
            vat_number,
        )
        partner = self.env.context.get("vat_partner")
        if partner:
            partner.update({"vies_passed": False})
        return res

    @api.model
    def vies_vat_check(self, country_code, vat_number):
        partner = self.env.context.get("vat_partner")
        if partner:
            # If there's an exception checking VIES, the upstream method will
            # call simple_vat_check and thus the flag will be removed
            partner.update({"vies_passed": True})
        res = super(ResPartner, self).vies_vat_check(country_code, vat_number)
        if not res:
            return self.simple_vat_check(country_code, vat_number)
        return res

    @api.constrains("vat", "country_id")
    def check_vat(self):
        for partner in self:
            partner = partner.with_context(vat_partner=partner)
            super(ResPartner, partner).check_vat()
        return True
