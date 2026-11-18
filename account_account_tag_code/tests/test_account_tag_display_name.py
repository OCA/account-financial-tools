# Copyright 2014-2022 Acsone (http://acsone.eu)
# Copyright 2016-2022 Akretion (http://www.akretion.com/)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests.common import TransactionCase


class TestAccountTag(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tag = cls.env["account.account.tag"].create(
            {
                "name": "Test Tag Name",
            }
        )

    def test_display_name_without_code(self):
        self.assertEqual(self.tag.display_name, self.tag.name)

    def test_display_name_with_code(self):
        self.tag.code = "Test"
        self.assertEqual(self.tag.display_name, f"[{self.tag.code}] {self.tag.name}")
