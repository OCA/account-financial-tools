# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.tests import common


class LawsuitRequisitionTester(common.TransactionCase):

    def setUp(self):
        """Initialize credit control level mock to test fees computations"""
        super(LawsuitRequisitionTester, self).setUp()
        self.currency_model = self.env['res.currency']

        browse_ref = self.browse_ref

        self.euro = browse_ref('base.EUR')

        level_model = self.env['credit.control.policy.level']
        self.level_lawsuit = level_model.new({
            'dunning_fixed_amount': 5.0,
            'currency_id': self.euro,
            'dunning_type': 'fixed',
            'need_lawsuit': True,
        })

        self.level_no_lawsuit = level_model.new({
            'dunning_fixed_amount': 5.0,
            'currency_id': self.euro,
            'dunning_type': 'fixed',
            'need_lawsuit': False,
        })

        credit_line1 = self.env['credit.control.line'].new({
            'policy_level_id': self.level_lawsuit,
            'currency_id': self.euro,
            'dunning_fees_amount': 10.0,
        })

        credit_line2 = self.env['credit.control.line'].new({
            'policy_level_id': self.level_lawsuit,
            'currency_id': self.euro,
            'dunning_fees_amount': 10.0,
        })

        no_lawsuit_credit_line_1 = self.env['credit.control.line'].new({
            'policy_level_id': self.level_no_lawsuit,
            'currency_id': self.euro,
            'dunning_fees_amount': 33.0,
        })
        self.no_lawsuit_credit_line = no_lawsuit_credit_line_1
        no_lawsuit_credit_line_2 = self.env['credit.control.line'].new({
            'policy_level_id': self.level_no_lawsuit,
            'currency_id': self.euro,
            'dunning_fees_amount': 33.0,
        })

        self.lawsuit_invoice_1 = self.env['account.invoice'].new({
            'partner_id': browse_ref("base.res_partner_12"),
            'currency_id': self.euro,
            'residual': 50.0,
            'amount_total': 130.0,
            'credit_control_line_ids': credit_line1 + credit_line2,
        })

        self.lawsuit_invoice_2 = self.env['account.invoice'].new({
            'partner_id': browse_ref("base.res_partner_12"),
            'currency_id': self.euro,
            'residual': 50.0,
            'amount_total': 130.0,
            'credit_control_line_ids': credit_line1 + credit_line2,
        })

        no_lawsuit_lines = no_lawsuit_credit_line_1 + no_lawsuit_credit_line_2
        self.non_lawsuit_invoice_1 = self.env['account.invoice'].new({
            'partner_id': browse_ref("base.res_partner_12"),
            'currency_id': self.euro,
            'residual': 50.0,
            'amount_total': 130.0,
            'credit_control_line_ids': no_lawsuit_lines,
        })

        schedule = self.env['lawsuit.fees.schedule'].create({
            'name': 'r1',
            'product_id': browse_ref('product.product_product_3').id,
            'currency_id': self.euro.id,
        })

        self.env['lawsuit.fees.schedule.line'].create({
            'schedule_id': schedule.id,
            'open_amount': 0,
            'fees': 30
        })

        self.env['lawsuit.fees.schedule.line'].create({
            'schedule_id': schedule.id,
            'open_amount': 500,
            'fees': 70,
        })

        self.lawsuit_office = self.env['lawsuit.office'].create({
            'name': 'Lausanne',
            'partner_id': browse_ref('base.res_partner_13').id,
            'fees_schedule_id': schedule.id,
        })

        self.env['res.better.zip'].create({
            'name': '1001',
            'city': 'lausanne',
            'lawsuit_office_id': self.lawsuit_office.id,
        })

    def test_filter(self):
        """Test filter invoices"""
        wiz_model = self.env['credit.control.lawsuit.printer']
        res = wiz_model._filter_lawsuit_invoices(
            self.lawsuit_invoice_1 + self.lawsuit_invoice_2 +
            self.non_lawsuit_invoice_1
        )
        self.assertEqual(res, self.lawsuit_invoice_1 + self.lawsuit_invoice_2)

    def test_mark(self):
        invoice = self.lawsuit_invoice_1
        invoice.credit_control_line_ids += self.no_lawsuit_credit_line
        wiz_model = self.env['credit.control.lawsuit.printer']
        res = wiz_model._mark_invoices_as_filed(self.lawsuit_invoice_1)
        self.assertEqual(res, self.no_lawsuit_credit_line)

    def test_get_fees(self):
        schedule = self.lawsuit_office.fees_schedule_id
        fees = schedule.get_fees_from_amount(50.00)
        self.assertEqual(fees, 30)
        fees = schedule.get_fees_from_amount(550.00)
        self.assertEqual(fees, 70)

    def test_get_fees_from_invoices(self):
        schedule = self.lawsuit_office.fees_schedule_id
        fees = schedule._get_fees_from_invoices([self.lawsuit_invoice_1,
                                                 self.lawsuit_invoice_2])
        self.assertEqual(fees, 30)
        self.lawsuit_invoice_1.residual = 800
        schedule = self.lawsuit_office.fees_schedule_id
        fees = schedule._get_fees_from_invoices([self.lawsuit_invoice_1,
                                                 self.lawsuit_invoice_2])
