# Copyright 2022-2023 Moduon Team S.L. <info@moduon.team>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest import mock

from odoo.tests import common


class TestConfigSettings(common.TransactionCase):
    def setUp(self):
        super(TestConfigSettings, self).setUp()
        self.company = self.env.user.company_id
        self.partner1_test = self.env["res.partner"].create(
            {
                "name": "Test partner",
                "is_company": True,
                "vat": "ESB87530432",
                "country_id": self.env.ref("base.be").id,
            }
        )
        self.partner2_test = self.env["res.partner"].create(
            {
                "name": "Test partner2",
                "is_company": True,
                "vat": "ESB87530432",
            }
        )
        self.vatnumber_path = "odoo.addons.base_vat.models.res_partner.check_vies"

    def test_execute_update_check_vies_validate(self):
        with mock.patch(self.vatnumber_path) as mock_vatnumber:
            self.company.vat_check_vies = True
            mock_vatnumber.check_vies.return_value = True
            self.env["res.config.settings"].execute_update_check_vies()
            self.assertTrue(self.partner1_test.vies_passed)
            self.assertFalse(self.partner2_test.vies_passed)

    def test_execute_update_check_vies_no_validate(self):
        with mock.patch(self.vatnumber_path) as mock_vatnumber:
            self.company.vat_check_vies = False
            mock_vatnumber.check_vies.return_value = False
            self.env["res.config.settings"].execute_update_check_vies()
            self.assertFalse(self.partner1_test.vies_passed)
            self.assertFalse(self.partner2_test.vies_passed)
