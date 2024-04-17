# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from stdnum.exceptions import InvalidComponent

from odoo.exceptions import ValidationError
from odoo.tests import common


class TestResPartner(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        def check_vies(vat_number):
            return {"valid": vat_number == "ESB87530432"}

        super().setUpClass()
        cls.company = cls.env.user.company_id
        cls.company.vat_check_vies = True
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "is_company": True,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.vatnumber_path = "odoo.addons.base_vat.models.res_partner.check_vies"

        cls._vies_check_func = check_vies

    def test_validate_valid_vat_vies(self):
        with patch(self.vatnumber_path, type(self)._vies_check_func):
            values = {"vat": "ESB87530432"}
            self.partner.write(values)
            self.assertEqual(self.partner.vat, "ESB87530432")

    def test_validate_invalid_vat_unavailable_vies(self):
        with patch(self.vatnumber_path, side_effect=Exception()):
            values = {"vat": "ESB8753043"}
            with self.assertRaises(ValidationError):
                self.partner.write(values)

    def test_validate_invalid_vies_vat(self):
        with patch(self.vatnumber_path, side_effect=InvalidComponent()):
            values = {"vat": "ESB87530432"}
            with self.assertRaises(ValidationError):
                self.partner.write(values)
