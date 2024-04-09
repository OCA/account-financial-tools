# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2016 Tecnativa - Sergio Teruel
# Copyright 2017 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import mock
from odoo.tests import common
from odoo.tools import mute_logger

MOCK_PATH = "odoo.addons.base_vat.models.res_partner.check_vies"


class TestResPartner(common.TransactionCase):
    def setUp(self):
        super(TestResPartner, self).setUp()
        self.company = self.env.user.company_id
        self.company.vat_check_vies = True
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test partner",
                "country_id": self.ref("base.es"),
            }
        )

    def test_validate_vat_vies(self):
        with mock.patch(MOCK_PATH, return_value={"valid": True}) as mocker:
            self.partner.write({"vat": "ESB87530432"})
            self.assertEqual(self.partner.vies_passed, True)
            mocker.assert_called_once_with("ESB87530432")

    @mute_logger("odoo.addons.base_vat.models.res_partner")
    def test_exception_vat_vies(self):
        with mock.patch(MOCK_PATH, side_effect=Exception) as mocker:
            self.partner.write({"vat": "ESB87530432"})
            self.assertEqual(self.partner.vies_passed, False)
            mocker.assert_called_once_with("ESB87530432")

    def test_no_validate_vat(self):
        with mock.patch(MOCK_PATH, return_value={"valid": False}) as mocker:
            self.partner.write({"vat": "ESB87530432"})
            self.assertEqual(self.partner.vies_passed, False)
            mocker.assert_called_once_with("ESB87530432")
