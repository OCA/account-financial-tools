# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPermanentLockDate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.new_company = self.env["res.company"].create(
            {"name": "My little test company"}
        )

    def test_set_fiscal_year_lock_date(self):
        self.new_company.write({"fiscalyear_lock_date": "2020-12-31"})
        with self.assertRaises(UserError):
            self.new_company.write({"fiscalyear_lock_date": False})
        with self.assertRaises(UserError):
            self.new_company.write({"fiscalyear_lock_date": "2020-11-30"})
        # Test there's no error if you write the same date
        self.new_company.write({"fiscalyear_lock_date": "2020-12-31"})
        # Test there's no error if you move forward
        # also test there is no bug if the date is a datetime object
        self.new_company.write(
            {"fiscalyear_lock_date": fields.Date.from_string("2021-01-31")}
        )
