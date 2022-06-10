# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2016 Tecnativa - Sergio Teruel
# Copyright 2017 Tecnativa - David Vidal
# Copyright 2022 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import mock

from odoo.exceptions import ValidationError
from odoo.tests import common


class TestResPartner(common.TransactionCase):
    def setUp(self):
        super(TestResPartner, self).setUp()
        self.company = self.env.user.company_id
        self.company.vat_check_vies = True
        self.partner = self.env["res.partner"].create(
            {"name": "Test partner", "is_company": True}
        )
        self.vatnumber_path = "odoo.addons.base_vat.models.res_partner.check_vies"

    def test_validate_vat_vies(self):
        with mock.patch(self.vatnumber_path) as mock_vatnumber:
            mock_vatnumber.check_vies.return_value = True
            self.partner.vat = "ESB87530432"
            self.partner.country_id = self.env.ref("base.be")
            self.assertEqual(self.partner.vies_passed, True)

    def test_exception_vat_vies(self):
        with mock.patch(self.vatnumber_path) as mock_vatnumber:
            mock_vatnumber.check_vies.side_effect = Exception()
            self.partner.vat = "ESB87530432"
            self.assertEqual(self.partner.vies_passed, False)

    def test_no_validate_vat(self):
        with mock.patch(self.vatnumber_path) as mock_vatnumber:
            mock_vatnumber.check_vies.return_value = False
            self.partner.vat = "ESB87530432"
            self.assertEqual(self.partner.vies_passed, False)

    def test_validate_simple_vat_vies(self):
        with mock.patch(self.vatnumber_path) as mock_vatnumber:
            self.company.vat_check_vies = False
            mock_vatnumber.check_vies.return_value = False
            self.partner.vat = "MXGODE561231GR8"
            self.partner.country_id = self.env.ref("base.mx")
            self.assertEqual(self.partner.vies_passed, False)

    def test_validate_vies_passed_false_when_vat_set_to_false(self):
        with mock.patch(self.vatnumber_path) as mock_vatnumber:
            mock_vatnumber.check_vies.return_value = True
            self.partner.vat = "ESB87530432"
            self.partner.country_id = self.env.ref("base.be")
            self.assertEqual(self.partner.vies_passed, True)
            self.partner.vat = False
            self.assertEqual(self.partner.vies_passed, False)

    def test_validate_wrong_vat_shows_simple_message(self):
        with self.assertRaisesRegex(ValidationError, "does not seem to be valid"):
            self.partner.vat = "ES11111111A"
