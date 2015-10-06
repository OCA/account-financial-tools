# -*- coding: utf-8 -*-
# License AGPL-3: Antiun Ingenieria S.L. - Antonio Espinosa
# See README.rst file on addon root folder for more details

from openerp.tests.common import TransactionCase


class TestResPartner(TransactionCase):

    def setUp(self):
        super(TestResPartner, self).setUp()
        self.m_partner = self.env['res.partner']
        self.m_company = self.env['res.company']
        self.company = self.m_company.browse(self.ref('base.main_company'))
        self.partner = self.m_partner.browse(self.ref('base.res_partner_1'))

    def test_split_vat(self):
        cases = (
            # vat, country, => vat_country, vat_number
            ('ESB12345678', False, 'ES', 'B12345678'),
            ('B12345678', False, False, 'B12345678'),
            ('1EB12345678', False, False, '1EB12345678'),
            ('ESB12345678', 'DE', 'ES', 'B12345678'),
            ('B12345678', 'ES', 'ES', 'B12345678'),
        )
        for vat, country, vat_country, vat_number in cases:
            res_country, res_number = self.m_partner._split_vat(vat, country)
            self.assertEqual(res_country, vat_country)
            self.assertEqual(res_number, vat_number)

    def _test_validate_vat(self, cases):
        for vat, vat_country, res_vat, res_country, res_vies in cases:
            self.partner.write({
                'vat': vat,
                'vat_country': vat_country,
            })
            self.assertEqual(self.partner.vat, res_vat)
            self.assertEqual(self.partner.vat_country, res_country)
            self.assertEqual(self.partner.vies_passed, res_vies)

    def test_validate_vat_vies(self):
        """
        Validate VAT when company 'vat_check_vies' option is True
        All VATs are valid, but some are not signed up in VIES database
        """
        self.company.vat_check_vies = True
        cases = (
            # vat, vat_country => vat, vat_country, vies_passed
            # VATs signed up in VIES
            ('B84718550', 'ES', 'ESB84718550', 'ES', True),
            ('ESB84718550', False, 'ESB84718550', 'ES', True),
            ('222070543', 'DE', 'DE222070543', 'DE', True),
            ('DE222070543', False, 'DE222070543', 'DE', True),
            # Valid VATs don't signed up in VIES
            ('253130868', 'DE', '253130868', 'DE', False),
            ('DE253130868', False, '253130868', 'DE', False),
            ('B87286357', 'ES', 'B87286357', 'ES', False),
            ('ESB87286357', False, 'B87286357', 'ES', False),
        )
        self._test_validate_vat(cases)

    def test_validate_vat_no_vies(self):
        """
        Validate VAT when company 'vat_check_vies' option is False
        """
        self.company.vat_check_vies = False
        cases = (
            # vat, vat_country => vat, vat_country, vies_passed
            ('ESB84718550', False, 'ESB84718550', 'ES', False),
            ('B84718550', 'ES', 'B84718550', 'ES', False),
            ('DE222070543', False, 'DE222070543', 'DE', False),
            ('222070543', 'DE', '222070543', 'DE', False),
            ('DE253130868', False, 'DE253130868', 'DE', False),
            ('253130868', 'DE', '253130868', 'DE', False),
            ('ESB87286357', False, 'ESB87286357', 'ES', False),
            ('B87286357', 'ES', 'B87286357', 'ES', False),
        )
        self._test_validate_vat(cases)
