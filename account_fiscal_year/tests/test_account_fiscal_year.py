# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import openerp.tests.common as common
from openerp import fields
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
                           DEFAULT_SERVER_DATETIME_FORMAT)


def to_odoo_datetime(date):
    return date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)


def to_odoo_date(date):
    return date.strftime(DEFAULT_SERVER_DATE_FORMAT)


class TestAccountFiscalYear(common.TransactionCase):

    def setUp(self):
        super(TestAccountFiscalYear, self).setUp()
        self.today_date = fields.Date.from_string(fields.Date.today())
        self.company = self.env.ref('base.main_company')

    def test_example(self):
        demo_date_range = self.env['date.range'].create(
            {'name': 'FY%s' % (self.today_date.year),
             'date_start': '%s-01-01' % self.today_date.year,
             'date_end': '%s-12-31' % self.today_date.year,
             'type_id': self.env.ref('account_fiscal_year.fiscalyear').id,
             'company_id': self.company.id,
             'active': True})
        result = self.company.compute_fiscalyear_dates(self.today_date)
        self.assertEqual(to_odoo_datetime(result['date_from']),
                         demo_date_range.date_start)
        self.assertEqual(to_odoo_datetime(result['date_to']),
                         demo_date_range.date_end)

    def test_example2(self):
        demo_date_range = self.env['date.range'].create(
            {'name': 'FY%s' % (self.today_date.year),
             'date_start': '%s-03-01' % self.today_date.year,
             'date_end': '%s-12-31' % self.today_date.year,
             'type_id': self.env.ref('account_fiscal_year.fiscalyear').id,
             'company_id': self.company.id,
             'active': True})
        result = self.company.compute_fiscalyear_dates(self.today_date)
        if to_odoo_date(self.today_date) >= demo_date_range.date_start:
            self.assertEqual(to_odoo_datetime(result['date_from']),
                             demo_date_range.date_start)
            self.assertEqual(to_odoo_datetime(result['date_to']),
                             demo_date_range.date_end)
