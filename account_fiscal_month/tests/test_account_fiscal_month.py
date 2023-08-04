# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestAccountFiscalMonth(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.DateRangeObj = cls.env["date.range"]
        cls.DateRangeType = cls.env["date.range.type"]

        cls.company = cls.env.ref("base.main_company")

        cls.date_range_type = cls.DateRangeType.create(
            {"name": "Other Type", "allow_overlap": False}
        )
        cls.date_range_type_month = cls.env.ref(
            "account_fiscal_month.date_range_fiscal_month"
        )

        cls.date_range_1 = cls.DateRangeObj.create(
            {
                "name": "Other",
                "date_start": "2017-01-01",
                "date_end": "2017-01-31",
                "type_id": cls.date_range_type.id,
                "company_id": cls.company.id,
            }
        )

        cls.date_range_january_2017 = cls.DateRangeObj.create(
            {
                "name": "January 2017",
                "date_start": "2017-01-01",
                "date_end": "2017-01-31",
                "type_id": cls.date_range_type_month.id,
                "company_id": cls.company.id,
            }
        )
        cls.date_range_january_no_comp_2017 = cls.DateRangeObj.create(
            {
                "name": "January 2017",
                "date_start": "2017-01-01",
                "date_end": "2017-01-31",
                "type_id": cls.date_range_type_month.id,
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
