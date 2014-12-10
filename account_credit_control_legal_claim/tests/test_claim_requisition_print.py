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
from mock import MagicMock, patch
import openerp.tests.common as test_common


class ClaimRequisitionTester(test_common.TransactionCase):

    def setUp(self):
        """Initialaize credit control level mock to test fees computations"""
        super(ClaimRequisitionTester, self).setUp()
        self.currency_model = self.registry('res.currency')
        self.euro = self.currency_model.search(self.cr, self.uid,
                                               [('name', '=', 'EUR')])
        self.assertTrue(self.euro)
        self.euro = self.registry('res.currency').browse(self.cr,
                                                         self.uid,
                                                         self.euro[0])

        self.euro_level = MagicMock(name='Euro policy level')
        self.euro_level.dunning_fixed_amount = 5.0
        self.euro_level.dunning_currency_id = self.euro
        self.euro_level.dunning_type = 'fixed'
        self.euro_level.is_legal_claim = True

        self.euro_level_no_claim = MagicMock(name='Euro policy level no claim')
        self.euro_level_no_claim.dunning_fixed_amount = 5.0
        self.euro_level_no_claim.dunning_currency_id = self.euro
        self.euro_level_no_claim.dunning_type = 'fixed'
        self.euro_level_no_claim.is_legal_claim = False

        credit_line = MagicMock(name='Euro credit line')
        credit_line.policy_level_id = self.euro_level
        credit_line.currency_id = self.euro
        credit_line.dunning_fees_amount = 10

        no_claim_credit_line = MagicMock(name='No claim credit line')
        no_claim_credit_line.policy_level_id = self.euro_level_no_claim
        no_claim_credit_line.currency_id = self.euro
        no_claim_credit_line.dunning_fees_amount = 33
        self.credit_line = credit_line
        self.no_claim_credit_line = no_claim_credit_line

        self.claim_invoice_1 = MagicMock(name='Claim Invoice 1')
        self.claim_invoice_1.partner_id = self.browse_ref("base.res_partner_12")
        self.claim_invoice_1.currency_id = self.euro
        self.claim_invoice_1.residual = 50.00
        self.claim_invoice_1.amount_total = 130.00
        self.claim_invoice_1.credit_control_line_ids = [credit_line,
                                                        credit_line]

        self.claim_invoice_2 = MagicMock(name='Claim Invoice 1')
        self.claim_invoice_2.partner_id = self.browse_ref("base.res_partner_12")
        self.claim_invoice_2.currency_id = self.euro
        self.claim_invoice_2.residual = 50.00
        self.claim_invoice_2.amount_total = 130.00
        self.claim_invoice_2.credit_control_line_ids = [credit_line,
                                                        credit_line]

        self.non_claim_invoice_1 = MagicMock(name='Non Claim Invoice 1')
        self.non_claim_invoice_1.partner_id = self.browse_ref("base.res_partner_12")
        self.non_claim_invoice_1.currency_id = self.euro
        self.non_claim_invoice_1.residual = 50.00
        self.non_claim_invoice_1.amount_total = 130.00
        self.non_claim_invoice_1.credit_control_line_ids = [no_claim_credit_line,
                                                            no_claim_credit_line]

        scheme_id = self.registry('legal.claim.fees.scheme').create(
            self.cr,
            self.uid,
            {
                'name': 'r1',
                'product_id': self.browse_ref('product.product_product_3').id,
                'currency_id': self.euro.id,
            }
        )

        self.registry('legal.claim.fees.scheme.line').create(
            self.cr,
            self.uid,
            {
                'claim_scheme_id': scheme_id,
                'open_amount': 0,
                'fees': 30
            }
        )

        self.registry('legal.claim.fees.scheme.line').create(
            self.cr,
            self.uid,
            {
                'claim_scheme_id': scheme_id,
                'open_amount': 500,
                'fees': 70,
            }
        )

        claim_office_id = self.registry('legal.claim.office').create(
            self.cr,
            self.uid,
            {
                'name': 'Lausanne',
                'partner_id': self.browse_ref('base.res_partner_13').id,
                'fees_scheme_id': scheme_id,
            }
        )

        self.registry('res.better.zip').create(
            self.cr,
            self.uid,
            {
                'name': '1001',
                'city': 'lausanne',
                'claim_office_id': claim_office_id,
            }
        )

        self.claim_office = self.registry('legal.claim.office').browse(
            self.cr,
            self.uid,
            claim_office_id,
        )

    def test_00_filter(self):
        """Test filter invoices"""
        wiz_model = self.registry('credit.control.legal.claim.printer')
        res = wiz_model._filter_claim_invoices(self.cr, self.uid,
                                               [self.claim_invoice_1,
                                                self.claim_invoice_2,
                                                self.non_claim_invoice_1])
        self.assertEqual(res, [self.claim_invoice_1,
                               self.claim_invoice_2])

    def test_01_mark(self):
        self.claim_invoice_1.credit_control_line_ids.append(self.no_claim_credit_line)
        wiz_model = self.registry('credit.control.legal.claim.printer')
        target = 'openerp.osv.orm.BaseModel.write'
        with patch(target, MagicMock()):
            res = wiz_model._mark_invoice_as_claimed(self.cr,
                                                     self.uid,
                                                     self.claim_invoice_1)
        self.assertEqual(res, [self.no_claim_credit_line])

    def test_02_get_fees(self):
        scheme  = self.claim_office.fees_scheme_id
        fees = scheme.get_fees_from_amount(50.00)
        self.assertEqual(fees, 30)
        fees = scheme.get_fees_from_amount(550.00)
        self.assertEqual(fees, 70)

    def test_03_get_fees_from_invoices(self):
        scheme  = self.claim_office.fees_scheme_id
        fees = scheme._get_fees_from_invoices([self.claim_invoice_1,
                                               self.claim_invoice_1])
        self.assertEqual(fees, 30)
        self.claim_invoice_1.residual = 800
        scheme  = self.claim_office.fees_scheme_id
        fees = scheme._get_fees_from_invoices([self.claim_invoice_1,
                                               self.claim_invoice_1])
