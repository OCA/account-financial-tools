import logging

from odoo import api, models

_LOGGER = logging.getLogger(__name__)

try:
    import vatnumber
except ImportError:
    _LOGGER.warning(
        "VAT validation partially unavailable "
        "because the `vatnumber` Python library cannot be found. "
        "Install it to support more countries, for example with "
        "easy_install vatnumber`."
    )
    vatnumber = None


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def vies_vat_check(self, country_code, vat_number):
        try:
            # Validate against  VAT Information Exchange System (VIES)
            # see also http://ec.europa.eu/taxation_customs/vies/
            return vatnumber.check_vies(country_code.upper() + vat_number)
        except Exception:
            if self.env.user.company_id.must_validate_vat:
                return False
                # see http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl
            # Fault code may contain INVALID_INPUT, SERVICE_UNAVAILABLE, MS_UNAVAILABLE,
            # TIMEOUT or SERVER_BUSY. There is no way we can validate the input
            # with VIES if any of these arise, including the first one (it means invalid
            # country code or empty VAT number), so we fall back to the simple check.
            return self.simple_vat_check(country_code, vat_number)
