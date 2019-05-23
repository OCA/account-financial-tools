# -*- coding: utf-8 -*-
# Copyright 2017-2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp.addons.account.tests.account_test_classes\
    import AccountingTestCase


class TestAccountCostCenter(AccountingTestCase):

    def test_invoice_costcenter(self):
        Account = self.env['account.account']
        CostCenter = self.env['account.cost.center']
        InvLine = self.env['account.invoice.line']

        acc_rec = self.env.ref('account.data_account_type_receivable')
        acc_exp = self.env.ref('account.data_account_type_expenses')
        invoice_account = Account.search([
            ('user_type_id', '=', acc_rec.id)
        ], limit=1).id
        invoice_line_account = Account.search([
            ('user_type_id', '=', acc_exp.id)],
            limit=1).id

        invoice = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': invoice_account,
            'type': 'in_invoice',
        })

        line1 = InvLine.create({
            'product_id': self.env.ref('product.product_product_2').id,
            'quantity': 1.0,
            'price_unit': 100.0,
            'invoice_id': invoice.id,
            'name': 'product that cost 100',
            'account_id': invoice_line_account,
        })
        empty_cost_center = CostCenter.browse()
        self.assertTrue(
            (line1.cost_center_id == empty_cost_center),
            "Default cost center per line not set")

        costcenter = CostCenter.create({
            'name': 'Cost Center Test',
            'code': 'CC1',
            'company_id': self.env.user.company_id.id
        })
        invoice.cost_center_id = costcenter

        line2 = InvLine.with_context(cost_center_id=costcenter.id).create({
            'product_id': self.env.ref('product.product_product_4').id,
            'quantity': 1.0,
            'price_unit': 130.0,
            'invoice_id': invoice.id,
            'name': 'product that cost 130',
            'account_id': invoice_line_account,
        })
        self.assertTrue(
            (line2.cost_center_id == costcenter),
            "Default cost center per line set")

        invoice.signal_workflow('invoice_open')
