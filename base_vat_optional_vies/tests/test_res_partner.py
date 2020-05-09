# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2016 Tecnativa - Sergio Teruel
# Copyright 2017 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import mock

from odoo.tests import common


class TestResPartner(common.TransactionCase):
    def setUp(self):
        super(TestResPartner, self).setUp()
        self.company = self.env.user.company_id
        self.company.vat_check_vies = True
        self.partner = self.env["res.partner"].create({"name": "Test partner"})
        self.vatnumber_path = "odoo.addons.base_vat.models.res_partner.vatnumber"

    def test_validate_vat_vies(self):
        with mock.patch(self.vatnumber_path) as mock_vatnumber:
            mock_vatnumber.check_vies.return_value = True
            self.partner.vat = "ESB87530432"
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
