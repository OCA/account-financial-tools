# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestAccountFiscalMonth(TransactionCase):
    def setUp(self):
        super(TestAccountFiscalMonth, self).setUp()
        self.DateRangeObj = self.env["date.range"]
        self.DateRangeType = self.env["date.range.type"]

        self.company = self.env.ref("base.main_company")

        self.date_range_type = self.DateRangeType.create(
            {"name": "Other Type", "allow_overlap": False}
        )
        self.date_range_type_month = self.env.ref(
            "account_fiscal_month.date_range_fiscal_month"
        )

        self.date_range_1 = self.DateRangeObj.create(
            {
                "name": "Other",
                "date_start": "2017-01-01",
                "date_end": "2017-01-31",
                "type_id": self.date_range_type.id,
                "company_id": self.company.id,
            }
        )

        self.date_range_january_2017 = self.DateRangeObj.create(
            {
                "name": "January 2017",
                "date_start": "2017-01-01",
                "date_end": "2017-01-31",
                "type_id": self.date_range_type_month.id,
                "company_id": self.company.id,
            }
        )
        self.date_range_january_no_comp_2017 = self.DateRangeObj.create(
            {
                "name": "January 2017",
                "date_start": "2017-01-01",
                "date_end": "2017-01-31",
                "type_id": self.date_range_type_month.id,
                "company_id": False,
            }
        )

    def test_00_delete_type(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.date_range_type.unlink()

    def test_01_delete_type_fiscal_month(self):
        with self.assertRaises(UserError):
            self.date_range_type_month.unlink()

    def test_02_search_date_range(self):
        january_2017_1st = Date.from_string("2017-01-01")
        date_ranges = self.company.find_daterange_fm(january_2017_1st)

        self.assertEqual(len(date_ranges), 1)
        self.assertEqual(date_ranges[0], self.date_range_january_2017)
