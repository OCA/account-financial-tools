# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2017 Tecnativa - David Vidal
# Copyright 2019 FactorLibre - Rodrigo Bonilla
# Copyright 2022 Wolfswerke Sachsen GmbH - Heiko Groeneweg
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models, _
import requests
from xml.etree import ElementTree as ET
import html


class ResPartner(models.Model):
    _inherit = "res.partner"

    vies_passed = fields.Boolean(string="VIES validation", readonly=True)
    vat_id_last_check_date = fields.Datetime("VAT-ID last checked date")
    vies_check_ids = fields.One2many('vies_vat_check_extension', 'res_partner_id')

    @api.model
    def simple_vat_check(self, country_code, vat_number):
        res = super(ResPartner, self).simple_vat_check(country_code, vat_number,)
        partner = self.env.context.get("vat_partner")
        if partner and self.vies_passed:
            # Can not be sure that this VAT is signed up in VIES
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
        else:
            if isinstance(res, bool): # Do not run extended check during module test with exception
                self.vies_vat_check_extended(country_code, vat_number)

        return res

    @api.constrains("vat", "country_id")
    def check_vat(self):
        for partner in self:
            partner = partner.with_context(vat_partner=partner)
            super(ResPartner, partner).check_vat()

    @api.model
    def vies_vat_check_extended(self, country_code, vat_number):
        company_id = self.company_id or self.env.company
        partner = self.env.context.get("vat_partner")
        if company_id.vat:
            company_country_code = company_id.vat[:2]
            company_vat_number = company_id.vat[2:]
        url = "https://ec.europa.eu/taxation_customs/vies/services/checkVatService"
        headers = {"content-type": "application/soap+xml"}
        body = """
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
                <soapenv:Header/>
                <soapenv:Body>
                    <urn:checkVatApprox>
                        <urn:countryCode>%s</urn:countryCode>
                        <urn:vatNumber>%s</urn:vatNumber>
                        <urn:requesterCountryCode>%s</urn:requesterCountryCode>
                        <urn:requesterVatNumber>%s</urn:requesterVatNumber>
            """ % (country_code, vat_number, company_country_code, company_vat_number)
        if partner.name:
            body += """<urn:traderName>%s</urn:traderName>
                        """ % html.escape(partner.name)
        if partner.street:
            body += """<urn:traderStreet>%s</urn:traderStreet>
                     """ % html.escape(partner.street)
        if partner.city:
            body += """<urn:traderCity>%s</urn:traderCity>
                     """ % html.escape(partner.city)
        if partner.zip:
            body += """<urn:traderPostcode>%s</urn:traderPostcode>
                     """ % html.escape(partner.zip)
        body += """</urn:checkVatApprox>
                     </soapenv:Body>
                 </soapenv:Envelope>
            """
        try:
            response = requests.post(url, data=body, headers=headers)
        except IOError:
            error_msg = _(
                "Something went wrong during VIES enquiry. Maybe your internet connection is lost.")
            raise self.env['res.config.settings'].get_config_warning(error_msg)
        if response:
            response_text = ET.fromstring(response.text)
            if response.status_code in (100, 200) and partner:
                nsp = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                       'urn': 'ec.europa.eu:taxud:vies:services:checkVat:types'}
                vals = {}
                for data in response_text.findall(
                    ".//{urn:ec.europa.eu:taxud:vies:services:checkVat:types}checkVatApproxResponse/"):
                    if data.text == 'true' or data.text == '1':
                        val = True
                    elif data.text in ('false', '2', '3'):
                        val = False
                    else:
                        val = data.text
                    vals[data.tag.replace('{urn:ec.europa.eu:taxud:vies:services:checkVat:types}',
                                          '').lower()] = val

                if vals['valid'] == True:
                    partner.update({"vies_passed": True})
                else:
                    partner.update({"vies_passed": False})
                date_string = vals['requestdate']
                partner.update({"vat_id_last_check_date": fields.datetime.strptime(date_string[:10], '%Y-%m-%d')})
                vals['res_partner_id'] = partner.id
                vals['name'] = partner.name + " - " + vals['requestdate']
                self.env['vies_vat_check_extension'].create(vals)@api.model
    def vies_vat_check_extended(self, country_code, vat_number):
        company_id = self.company_id or self.env.company
        partner = self.env.context.get("vat_partner")
        if company_id.vat:
            company_country_code = company_id.vat[:2]
            company_vat_number = company_id.vat[2:]
        else:
            error_msg = _(
                "You must set a valid VAT-ID in your company profile in order to use extended VAT validation by VIES.")
            raise self.env['res.config.settings'].get_config_warning(error_msg)
        url = "https://ec.europa.eu/taxation_customs/vies/services/checkVatService"
        headers = {"content-type": "application/soap+xml"}
        body = """
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
            <soapenv:Header/>
            <soapenv:Body>
                <urn:checkVatApprox>
                    <urn:countryCode>%s</urn:countryCode>
                    <urn:vatNumber>%s</urn:vatNumber>
                    <urn:requesterCountryCode>%s</urn:requesterCountryCode>
                    <urn:requesterVatNumber>%s</urn:requesterVatNumber>
        """ % (country_code, vat_number, company_country_code, company_vat_number )
        if partner.name:
            body += """<urn:traderName>%s</urn:traderName>
                    """ % html.escape(partner.name)
        if partner.street:
            body += """<urn:traderStreet>%s</urn:traderStreet>
                 """ % html.escape(partner.street)
        if partner.city:
            body += """<urn:traderCity>%s</urn:traderCity>
                 """ % html.escape(partner.city)
        if partner.zip:
            body += """<urn:traderPostcode>%s</urn:traderPostcode>
                 """ % html.escape(partner.zip)
        body += """</urn:checkVatApprox>
                 </soapenv:Body>
             </soapenv:Envelope>
        """
        try:
            response = requests.post(url, data=body, headers=headers)
        except IOError:
            error_msg = _(
                "Something went wrong during VIES enquiry. Maybe your internet connection is lost.")
            raise self.env['res.config.settings'].get_config_warning(error_msg)
        if response:
            response_text = ET.fromstring(response.text)
            if response.status_code in (100, 200) and partner:
                nsp = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                       'urn': 'ec.europa.eu:taxud:vies:services:checkVat:types'}
                vals= {}
                for data in response_text.findall(".//{urn:ec.europa.eu:taxud:vies:services:checkVat:types}checkVatApproxResponse/"):
                    if data.text == 'true' or data.text == '1':
                        val = True
                    elif data.text in ('false', '2', '3'):
                        val = False
                    else:
                        val = data.text
                    vals[data.tag.replace('{urn:ec.europa.eu:taxud:vies:services:checkVat:types}',
                                              '').lower()] = val

                if vals['valid'] == True:
                    partner.update({"vies_passed": True})
                else:
                    partner.update({"vies_passed": False})
                date_string = vals['requestdate']
                partner.update({"vat_id_last_check_date": fields.datetime.strptime(date_string[:10], '%Y-%m-%d')})
                vals['res_partner_id'] = partner.id
                vals['name'] = partner.name + " - " + vals['requestdate']
                self.env['vies_vat_check_extension'].create(vals)
