# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase


class TestAccountInvoiceCurrency(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(TestAccountInvoiceCurrency, self).setUp(*args, **kwargs)

        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        tax_group_taxes = self.env.ref('account.tax_group_taxes')
        self.account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.account_customer = self.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })
        self.journal_sale = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Tax for sale 10%',
            'type_tax_use': 'sale',
            'tax_group_id': tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 10.0,
        })
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.account_customer.id,
            'type': 'out_invoice',
            'journal_id': self.journal_sale.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test product',
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1,
                'invoice_line_tax_ids': [(6, 0, [self.tax.id])],
            })],
        })

    def test_amount_tax_signed(self):
        self.assertEqual(10.0, self.invoice.amount_tax_signed)
