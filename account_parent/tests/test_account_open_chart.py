# -*- coding: utf-8 -*-
# Copyright (C) 2016 Steigend IT Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAcountOpenChart(TransactionCase):

    def setUp(self):
        super(TestAcountOpenChart, self).setUp()
        self.company_id = self.ref('base.main_company')
        self.open_chart_obj = self.env['account.open.chart']

    def test_open_chart(self):
        open_chart_id = self.open_chart_obj.create({
            'company_id': self.company_id
        })

        # Test that the open chart cannot open window
        self.assertTrue(open_chart_id.account_chart_open_window())
