import logging

from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import SavepointCaseWithUserDemo

_logger = logging.getLogger(__name__)


class TestVatOnlineValidation(SavepointCaseWithUserDemo):
    def setUp(self):
        super(TestVatOnlineValidation, self).setUp()

    def test_partner_valid_vat(self):
        partner_1 = self.env["res.partner"].create(
            {
                "name": "partner_1",
                "street": "Legoland-Allee 3",
                "zip": "89312",
                "city": "Günzburg",
                "vat": "DE300136599",
                "country_id": self.env.ref("base.de").id,
                "is_company": True,
                "company_id": self.env.ref("base.main_company").id,
            }
        )

        self.assertEqual("DE300136599", partner_1["vat"], True)

    def test_partner_raise_invalid_vat(self):
        with self.assertRaises(ValidationError):
            self.env["res.partner"].create(
                {
                    "name": "partner_2",
                    "street": "Legoland-Allee 3",
                    "zip": "89312",
                    "city": "Günzburg",
                    "vat": "BE0477472702",
                    "is_company": True,
                    "country_id": self.env.ref("base.de").id,
                    "company_id": self.env.ref("base.main_company").id,
                }
            )
