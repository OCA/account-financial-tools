# -*- coding: utf-8 -*-
# Author: Sébastien Namèche
# Copyright 2016 Sébastien Namèche
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestCompute(TransactionCase):

    def setUp(self):
        """Initialize currencies for testing"""
        super(TestCompute, self).setUp()
        self.currency_usd_id = self.env.ref("base.USD").id
        self.currency_euro_id = self.env.ref("base.EUR").id
        self.env.ref('base.main_company').write(
            {'currency_id': self.currency_euro_id})

    def create_invoice(self, currency_id):
        """Create and open a test invoice"""
        partner_id = self.ref('base.res_partner_2')
        il_account = self.env['account.account'].search(
            [('user_type_id', '=',
              self.ref('account.data_account_type_revenue'))], limit=1)
        invoice = self.env['account.invoice'].create(
            {'partner_id': partner_id,
             'currency_id': currency_id,
             'invoice_line_ids': [(0, 0,
                                   {'name': 'test',
                                    'account_id': il_account.id,
                                    'price_unit': 100.00,
                                    'quantity': 10,
                                    })],
             })
        invoice.invoice_validate()
        return invoice

    def test_compute_same_currency(self):
        """Test the case where the currency invoice is the same of the company
        currency"""
        test_invoice = self.create_invoice(self.currency_euro_id)
        self.assertEqual(test_invoice.cc_amount_untaxed,
                         test_invoice.amount_untaxed)
        self.assertEqual(test_invoice.cc_amount_tax,
                         test_invoice.amount_tax)
        self.assertEqual(test_invoice.cc_amount_total,
                         test_invoice.amount_total)

    def test_compute_other_currency(self):
        """Test the case where the currency invoice is not the same of the company
        currency"""
        test_invoice = self.create_invoice(self.currency_usd_id)
        self.assertNotEqual(test_invoice.cc_amount_total,
                            test_invoice.amount_total)
        self.assertEqual(test_invoice.cc_amount_total,
                         test_invoice.cc_amount_tax +
                         test_invoice.cc_amount_untaxed)
        # FIXME: More tests required
