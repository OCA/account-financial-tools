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

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vies_passed = fields.Boolean(
        string="VIES validation passed", readonly=True)
    vat_country = fields.Selection(
        selection=[
            ('AT', _('Austria')),
            ('AL', _('Albania')),
            ('AR', _('Argentina')),
            ('BE', _('Belgium')),
            ('BG', _('Bulgaria')),
            ('CH', _('Switzerland')),
            ('CL', _('Chile')),
            ('CO', _('Colombia')),
            ('CY', _('Cyprus')),
            ('CZ', _('Czech Republic')),
            ('DE', _('Germany')),
            ('DK', _('Denmark')),
            ('EE', _('Estonia')),
            ('ES', _('Spain')),
            ('FI', _('Finland')),
            ('FR', _('France')),
            ('GB', _('United Kingdom')),
            ('GR', _('Greece (GR)')),
            ('EL', _('Greece (EL)')),
            ('HR', _('Croatia')),
            ('HU', _('Hungary')),
            ('IE', _('Ireland')),
            ('IT', _('Italy')),
            ('LT', _('Lithuania')),
            ('LU', _('Luxembourg')),
            ('LV', _('Latvia')),
            ('MT', _('Malta')),
            ('MX', _('Mexico')),
            ('NL', _('Netherlands')),
            ('NO', _('Norway')),
            ('PE', _('Peru')),
            ('PL', _('Poland')),
            ('PT', _('Portugal')),
            ('RO', _('Romania')),
            ('RU', _('Russian Federation')),
            ('SE', _('Sweden')),
            ('SI', _('Slovenia')),
            ('SK', _('Slovakia')),
            ('SM', _('San Marino')),
            ('TR', _('Turkey')),
            ('UA', _('Ukraine')),
        ], string="VAT country")

    def __init__(self, pool, cr):
        super(ResPartner, self).__init__(pool, cr)
        self._constraints = []

    @api.constrains('vat', 'vat_country')
    def check_vat(self):
        for partner in self:
            if (not self.env.context.get('avoid_check_vat') and
                    not partner.parent_id):
                if not partner.validate_vat():
                    raise ValidationError(_("VAT number is not valid"))

    def button_check_vat(self, cr, uid, ids, context=None):
        partner = self.browse(cr, uid, ids, context=context)
        if not partner.validate_vat():
            raise ValidationError(_("VAT number is not valid"))
        return True

    def _split_vat(self, vat, country=False):
        """
        @summary: Split Partner vat into country_code and number
        @result: (vat_country, vat_number)
        """
        vat_country = False
        vat_number = vat
        if vat and re.match(r'[A-Za-z]{2}', vat):
            vat_country = vat[:2].upper()
            vat_number = vat[2:].replace(' ', '')
        elif country:
            vat_country = country
        return vat_country, vat_number

    def validate_vat(self):
        if self.company_id.vat_check_vies:
            # VIES online check
            check_func = self.vies_vat_check
        else:
            # quick and partial off-line checksum validation
            check_func = self.simple_vat_check
        vat_country, vat_number = self._split_vat(self.vat, self.vat_country)
        if not check_func(vat_country, vat_number):
            _logger.info("VAT Number [%s] is not valid !" % vat_number)
            return False
        return True

    def _country_is_available(self, country_code):
        values = [v for v, _ in self._columns['vat_country'].selection]
        return country_code and country_code in values

    def simple_vat_check(self, country_code, vat_number):
        """
        Check the VAT number depending of the country.
        http://sima-pc.com/nif.php
        """
        if not self._country_is_available(country_code):
            # If no available country code, then this VAT is OK
            return True
        check_func_name = 'check_vat_' + country_code.lower()
        check_func = getattr(self, check_func_name, None) or \
            getattr(vatnumber, check_func_name, None)
        if not check_func:
            # No VAT validation available, then this VAT is OK
            return True
        res = check_func(vat_number)
        data = {}
        if res and country_code != self.vat_country:
            # If country code is indicated in vat number, copy to country field
            data['vat_country'] = country_code
        if res and vat_number != self.vat and self.company_id.vat_check_vies:
            # Only modify VAT if vat_check_vies option is True
            data['vat'] = vat_number
        if res and self.vies_passed and not self.company_id.vat_check_vies:
            # Can not be sure that this VAT is signed up in VIES
            data['vies_passed'] = False
        if data:
            self.with_context(avoid_check_vat=True).write(data)
        return res

    def vies_vat_check(self, country_code, vat_number):
        data = {}
        res = False
        try:
            # Validate against VAT Information Exchange System (VIES)
            # see also http://ec.europa.eu/taxation_customs/vies/
            vat = country_code + vat_number
            res = vatnumber.check_vies(vat)
            if res and not self.vies_passed:
                data['vies_passed'] = True
            if res and vat != self.vat:
                data['vat'] = vat
            if res and country_code != self.vat_country:
                data['vat_country'] = country_code
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
            res = self.simple_vat_check(country_code, vat_number)
            if self.vies_passed:
                data['vies_passed'] = False
        if data:
            self.with_context(avoid_check_vat=True).write(data)
        return res

    # Delete old api constraint defined in base_vat addon
    @api.multi
    def _validate_fields(self, field_names):
        self._constraints = [x for x in self._constraints if not 'vat' in x[2]]
        super(ResPartner, self)._validate_fields(field_names)
