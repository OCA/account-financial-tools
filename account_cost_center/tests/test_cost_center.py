# Copyright 2017-2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestAccountCostCenter(common.TransactionCase):

    def setUp(self):
        super(TestAccountCostCenter, self).setUp()

        acc_rec = self.env.ref('account.data_account_type_receivable')
        acc_exp = self.env.ref('account.data_account_type_expenses')
        self.invoice_account = self.env['account.account'].search([
            ('user_type_id', '=', acc_rec.id)
        ], limit=1).id
        self.invoice_line_account = self.env['account.account'].search([
            ('user_type_id', '=', acc_exp.id)],
            limit=1).id

        self.invoice1 = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': self.invoice_account,
            'type': 'in_invoice',
        })

        self.line1 = self.env['account.invoice.line'].create({
            'product_id': self.env.ref('product.product_product_2').id,
            'quantity': 1.0,
            'price_unit': 100.0,
            'invoice_id': self.invoice1.id,
            'name': 'product that cost 100',
            'account_id': self.invoice_line_account,
        })

        self.costcenter = self.env['account.cost.center'].create({
            'name': 'Cost Center Test',
            'code': 'CC1',
            'company_id': self.env.user.company_id.id
        })

        self.invoice2 = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': self.invoice_account,
            'type': 'in_invoice',
            'cost_center_id': self.costcenter.id,
        })

        self.line2 = self.env['account.invoice.line'].with_context(
            cost_center_id=self.costcenter.id).create({
                'product_id': self.env.ref('product.product_product_4').id,
                'quantity': 1.0,
                'price_unit': 130.0,
                'invoice_id': self.invoice2.id,
                'name': 'product that cost 130',
                'account_id': self.invoice_line_account,
            })

    def test_01_check_lines(self):
        self.assertFalse(
            self.line1.cost_center_id,
            "Default cost center per line not set")

        self.assertTrue(
            (self.line2.cost_center_id == self.costcenter),
            "Default cost center per line set")

    def test_02_confirm_invoice(self):
        self.invoice2.action_invoice_open()
        for move in self.invoice2.move_id.line_ids:
            cost_center = move.cost_center_id
            if move.name == 'product that cost 130':
                self.assertTrue(cost_center)
            else:
                self.assertFalse(cost_center)
