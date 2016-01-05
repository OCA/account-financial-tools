# -*- coding: utf-8 -*-
# License AGPL-3: Antiun Ingenieria S.L. - Antonio Espinosa
# See README.rst file on addon root folder for more details

import logging
import re
_logger = logging.getLogger(__name__)

try:
    import vatnumber
except ImportError:
    _logger.warning(
        "VAT validation partially unavailable because the `vatnumber` Python "
        "library cannot be found. Install it to support more countries, "
        "for example with `easy_install vatnumber` or "
        "`pip install vatnumber`.")
    vatnumber = None

from openerp import models, fields, api
from openerp.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vies_passed = fields.Boolean(
        string="VIES validation passed", readonly=True)

    def __init__(self, pool, cr):
        super(ResPartner, self).__init__(pool, cr)
        self._constraints = []

    @api.constrains('vat')
    def check_vat(self):
        for partner in self:
            if (not self.env.context.get('avoid_check_vat') and
                    not partner.parent_id):
                if not partner.validate_vat():
                    raise ValidationError(partner._construct_constraint_msg())

    @api.multi
    def button_check_vat(self):
        if not self.validate_vat():
            raise ValidationError(self._construct_constraint_msg())
        return True

    def _split_vat(self, vat, country=False):
        """
        @summary: Split Partner vat into country_code and number
        @result: (vat_country, vat_number)
        """
        vat_country = 'XX'
        vat_number = vat
        if vat and re.match(r'[A-Za-z]{2}', vat):
            vat_country = vat[:2].upper()
            vat_number = vat[2:].replace(' ', '')
        elif country:
            vat_country = country
        return vat_country, vat_number

    @api.multi
    def validate_vat(self):
        self.ensure_one()
        if self.company_id.vat_check_vies:
            # VIES online check
            check_func = self.vies_vat_optional_check
        else:
            # quick and partial off-line checksum validation
            check_func = self.simple_vat_optional_check
        vat_country, vat_number = self._split_vat(self.vat)
        if vat_number and vat_country == 'XX':
            _logger.info("VAT country not found!")
            raise ValidationError(self._construct_constraint_msg())
        if vat_number and not check_func(vat_country, vat_number):
            _logger.info("VAT Number [%s] is not valid !" % vat_number)
            return False
        return True

    @api.multi
    def simple_vat_optional_check(self, country_code, vat_number):
        """
        Check the VAT number depending of the country.
        http://sima-pc.com/nif.php
        """
        self.ensure_one()
        res = self.simple_vat_check(country_code.lower(), vat_number)
        data = {}
        if res and self.vies_passed and not self.company_id.vat_check_vies:
            # Can not be sure that this VAT is signed up in VIES
            data['vies_passed'] = False
        if res:
            vat = country_code + vat_number
            if self.vat != vat:
                data['vat'] = vat
        if data:
            self.with_context(avoid_check_vat=True).write(data)
        return res

    @api.multi
    def vies_vat_optional_check(self, country_code, vat_number):
        self.ensure_one()
        data = {}
        res = False
        try:
            # Validate against VAT Information Exchange System (VIES)
            # see also http://ec.europa.eu/taxation_customs/vies/
            vat = country_code + vat_number
            res = vatnumber.check_vies(vat)
            if res and not self.vies_passed:
                data['vies_passed'] = True
        except Exception:
            # See:
            #   http://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl
            # Fault code may contain INVALID_INPUT, SERVICE_UNAVAILABLE,
            # MS_UNAVAILABLE, TIMEOUT or SERVER_BUSY. There is no way we can
            # validate the input with VIES if any of these arise, including
            # the first one (it means invalid country code or empty
            # VAT number), so we fall back to the simple check.
            pass

        if not res:
            res = self.simple_vat_optional_check(country_code, vat_number)
            if self.vies_passed:
                data['vies_passed'] = False
        if res:
            vat = country_code + vat_number
            if self.vat != vat:
                data['vat'] = vat
        if data:
            self.with_context(avoid_check_vat=True).write(data)
        return res

    # Delete old api constraint defined in base_vat addon
    @api.multi
    def _validate_fields(self, field_names):
        self._constraints = [x for x in self._constraints if 'vat' not in x[2]]
        super(ResPartner, self)._validate_fields(field_names)
