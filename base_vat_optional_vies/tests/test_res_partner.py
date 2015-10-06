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
        for vat, res_vat, res_vies in cases:
            self.partner.write({
                'vat': vat,
            })
            self.assertEqual(self.partner.vat, res_vat)
            self.assertEqual(self.partner.vies_passed, res_vies)

    def test_validate_vat_vies(self):
        """
        Validate VAT when company 'vat_check_vies' option is True
        All VATs are valid, but some are not signed up in VIES database
        """
        self.company.vat_check_vies = True
        cases = (
            # vat => vat, vies_passed
            # VATs signed up in VIES
            ('ESB84718550', 'ESB84718550', True),
            ('de222070543', 'DE222070543', True),
            # Valid VATs don't signed up in VIES
            ('DE253130868', 'DE253130868', False),
            ('esB87286357', 'ESB87286357', False),
        )
        self._test_validate_vat(cases)

    def test_validate_vat_no_vies(self):
        """
        Validate VAT when company 'vat_check_vies' option is False
        """
        self.company.vat_check_vies = False
        cases = (
            # vat => vat, vies_passed
            ('ESB84718550', 'ESB84718550', False),
            ('de222070543', 'DE222070543', False),
            ('DE253130868', 'DE253130868', False),
            ('esB87286357', 'ESB87286357', False),
        )
        self._test_validate_vat(cases)
