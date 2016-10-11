# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestAccountFiscalYear(TransactionCase):

    def setUp(self):
        super(TestAccountFiscalYear, self).setUp()
        self.today_date = datetime.date.today() + relativedelta(years=100)
        self.company = self.env.ref('base.main_company')

    def test_compute_fiscalyear(self):
        """Check that a call to that Odoo's method returns the dates from
        a fiscal year date range if one exists for the given date
        """
        # check that the result  by default from 1/1 31/12
        result = self.company.compute_fiscalyear_dates(self.today_date)
        self.assertEquals(
            result['date_from'],
            datetime.date(self.today_date.year, 1, 1))
        self.assertEquals(
            result['date_to'],
            datetime.date(self.today_date.year, 12, 31))
        # create a fiscal year with different limits
        demo_date_range = self.env['date.range'].create(
            {'name': 'FY%s' % (self.today_date.year),
             'date_start': '%s-04-01' % self.today_date.year,
             'date_end': '%s-11-30' % self.today_date.year,
             'type_id': self.env.ref('account_fiscal_year.fiscalyear').id,
             'company_id': self.company.id,
             'active': True})
        result = self.company.compute_fiscalyear_dates(
            datetime.date(self.today_date.year, 5, 4))
        self.assertEqual(
            result['date_from'],
            fields.Date.from_string(demo_date_range.date_start))
        self.assertEqual(
            result['date_to'],
            fields.Date.from_string(demo_date_range.date_end))
