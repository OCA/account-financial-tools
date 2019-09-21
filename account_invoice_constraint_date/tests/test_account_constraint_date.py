# Copyright 2019 Sergio Corato <https://github.com/sergiocorato>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import timedelta

import odoo.tests.common as common
from odoo import fields
from odoo.exceptions import UserError


class TestAccountConstraintDate(common.TransactionCase):

    def setUp(self):
        super(TestAccountConstraintDate, self).setUp()
        self.a_purchase = self.env['account.account'].search([
            ('user_type_id', '=',
             self.env.ref('account.data_account_type_expenses').id)
        ], limit=1)

    def create_simple_invoice(self, date):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'type': 'in_invoice',
            'date': date,
        })
        self.env['account.invoice.line'].create({
            'product_id': self.env.ref('product.product_product_2').id,
            'quantity': 1.0,
            'invoice_id': invoice.id,
            'account_id': self.a_purchase.id,
            'price_unit': 50.0,
            'name': 'Invoice line',
            'invoice_line_tax_ids': [(4, self.env['account.tax'].search(
                [('type_tax_use', '=', 'purchase')], limit=1).id, 0)]
        })
        invoice.compute_taxes()
        return invoice

    def test_invoice_validate(self):
        date = fields.Datetime.to_string(
            fields.Datetime.today() - timedelta(days=50))
        invoice = self.create_simple_invoice(date)
        with self.assertRaises(UserError):
            invoice.action_invoice_open()
        invoice.date = fields.Date.today()
        invoice.action_invoice_open()
        self.assertTrue(invoice.state == 'open', 'Invoice was not created')
