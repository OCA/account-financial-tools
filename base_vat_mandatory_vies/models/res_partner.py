# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from stdnum.exceptions import InvalidComponent

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    vies_unavailable = fields.Boolean(store=False)

    @api.model
    def _run_vat_test(self, vat_number, default_country, partner_is_company=True):
        # Get company
        if self.env.context.get("company_id"):
            company = self.env["res.company"].browse(self.env.context["company_id"])
        else:
            company = self.env.company

        # Get check function: either simple syntactic check or call to VIES service
        eu_countries = self.env.ref("base.europe").country_ids
        if (
            company.vat_check_vies
            and default_country in eu_countries
            and partner_is_company
        ):
            return self._run_vies_test(vat_number, default_country)
        return super()._run_vat_test(
            vat_number, default_country, partner_is_company=partner_is_company
        )

    @api.model
    def _check_vies(self, vat):
        try:
            return super()._check_vies(vat)
        except InvalidComponent:
            raise InvalidComponent from None
        except Exception as e:
            self.vies_unavailable = True
            raise

    @api.model
    def vies_vat_check(self, country_code, vat_number):
        res = super().vies_vat_check(country_code, vat_number)
        if res and self.vies_unavailable:
            # leave the possibility to strictly check vies and not fallback on
            # simple vat check, in case the service is unavailable... This way it is
            # considered as invalid.
            if self.env.context.get("strict_vies"):
                return False
            else:
                return self.simple_vat_check(country_code, vat_number)
        return res
