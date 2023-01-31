# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2017 Tecnativa - David Vidal
# Copyright 2019 FactorLibre - Rodrigo Bonilla
# Copyright 2022 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models

from odoo.addons.base_vat.models.res_partner import _ref_vat


class ResPartner(models.Model):
    _inherit = "res.partner"

    vies_passed = fields.Boolean(string="VIES validation", readonly=True)

    @api.model
    def simple_vat_check(self, country_code, vat_number):
        res = super().simple_vat_check(country_code, vat_number)
        partner = self._context.get("vat_partner")
        if res is False and partner:
            partner.update({"vies_passed": False})
        elif partner:
            if self.env.context.get("company_id"):
                company = self.env["res.company"].browse(self.env.context["company_id"])
            else:
                company = self.env.company
            if company.vat_check_vies:
                self.vies_vat_check(country_code, vat_number)
        return res

    @api.model
    def vies_vat_check(self, country_code, vat_number):
        partner = self._context.get("vat_partner")
        res = super().vies_vat_check(country_code, vat_number)
        if res is False and partner:
            partner.update({"vies_passed": False})
        elif partner:
            partner.update({"vies_passed": True})
        return res

    @api.constrains("vat", "country_id")
    def check_vat(self):
        self.update({"vies_passed": False})
        for partner in self.sorted(lambda p: bool(p.commercial_partner_id)):
            partner = partner.with_context(vat_partner=partner)
            if (
                partner.commercial_partner_id
                and partner.commercial_partner_id != partner
            ):
                partner.update(
                    {"vies_passed": partner.commercial_partner_id.vies_passed}
                )
            else:
                super(ResPartner, partner).check_vat()
        return True

    @api.onchange("vat", "country_id")
    def _onchange_check_vies(self):
        self.update({"vies_passed": False})
        return super(
            ResPartner, self.with_context(vat_partner=self)
        )._onchange_check_vies()

    @api.model
    def _build_vat_error_message(self, country_code, wrong_vat, record_label):
        return "\n" + _(
            "The VAT number [%(wrong_vat)s] for %(record_label)s does not seem to be valid. "
            "\nNote: the expected format is %(expected_format)s",
            wrong_vat=wrong_vat,
            record_label=record_label,
            expected_format=_ref_vat.get(
                country_code, "'CC##' (CC=Country Code, ##=VAT Number)"
            ),
        )
