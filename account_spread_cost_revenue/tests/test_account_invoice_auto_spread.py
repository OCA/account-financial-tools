# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import convert_file
from odoo.modules.module import get_resource_path
from odoo.exceptions import UserError
from odoo.tests import common


class TestAccountInvoiceSpread(common.TransactionCase):

    def _load(self, module, *args):
        convert_file(
            self.cr,
            'account_spread_cost_revenue',
            get_resource_path(module, *args),
            {}, 'init', False, 'test', self.registry._assertion_report)

    def setUp(self):
        super().setUp()
        self._load('account', 'test', 'account_minimal_test.xml')

        type_receivable = self.env.ref('account.data_account_type_receivable')
        type_payable = self.env.ref('account.data_account_type_payable')
        type_revenue = self.env.ref('account.data_account_type_revenue')

        self.invoice_account = self.env['account.account'].create({
            'name': 'test_account_receivable',
            'code': '123',
            'user_type_id': type_receivable.id,
            'reconcile': True
        })

        self.account_payable = self.env['account.account'].create({
            'name': 'test_account_payable',
            'code': '321',
            'user_type_id': type_payable.id,
            'reconcile': True
        })

        self.account_revenue = self.env['account.account'].create({
            'name': 'test_account_revenue',
            'code': '864',
            'user_type_id': type_revenue.id,
            'reconcile': True
        })

        self.invoice_line_account = self.account_payable

        self.spread_account = self.env['account.account'].create({
            'name': 'test spread account_payable',
            'code': '765',
            'user_type_id': type_payable.id,
            'reconcile': True
        })

        partner = self.env['res.partner'].create({
            'name': 'Partner Name',
            'supplier': True,
        })

        # Purchase Invoice
        self.invoice = self.env['account.invoice'].create({
            'partner_id': partner.id,
            'account_id': self.invoice_account.id,
            'type': 'in_invoice',
        })
        self.invoice_line = self.env['account.invoice.line'].create({
            'quantity': 1.0,
            'price_unit': 1000.0,
            'invoice_id': self.invoice.id,
            'name': 'product that cost 1000',
            'account_id': self.invoice_account.id,
        })

        # Sales Invoice
        self.invoice_2 = self.env['account.invoice'].create({
            'partner_id': partner.id,
            'account_id': self.invoice_account.id,
            'type': 'out_invoice',
        })
        self.invoice_line_2 = self.env['account.invoice.line'].create({
            'quantity': 1.0,
            'price_unit': 1000.0,
            'invoice_id': self.invoice_2.id,
            'name': 'product that cost 1000',
            'account_id': self.invoice_line_account.id,
        })

    def test_01_no_auto_spread_sheet(self):

        self.env['account.spread.template'].create({
            'name': 'test',
            'spread_type': 'purchase',
            'period_number': 5,
            'period_type': 'month',
            'spread_account_id': self.account_payable.id,
            'spread_journal_id': self.ref(
                'account_spread_cost_revenue.expenses_journal'),
            'auto_spread': False,  # Auto Spread = False
            'auto_spread_ids': [
                (0, 0, {'account_id': self.invoice_account.id})]
        })

        self.assertFalse(self.invoice_line.spread_id)
        self.invoice.action_invoice_open()
        self.assertFalse(self.invoice_line.spread_id)

    def test_02_new_auto_spread_sheet_purchase(self):

        self.env['account.spread.template'].create({
            'name': 'test 1',
            'spread_type': 'purchase',
            'period_number': 5,
            'period_type': 'month',
            'spread_account_id': self.account_payable.id,
            'spread_journal_id': self.ref(
                'account_spread_cost_revenue.expenses_journal'),
            'auto_spread': True,  # Auto Spread
            'auto_spread_ids': [
                (0, 0, {'account_id': self.invoice_account.id})]
        })
        template2 = self.env['account.spread.template'].create({
            'name': 'test 2',
            'spread_type': 'purchase',
            'period_number': 5,
            'period_type': 'month',
            'spread_account_id': self.account_payable.id,
            'spread_journal_id': self.ref(
                'account_spread_cost_revenue.expenses_journal'),
            'auto_spread': True,  # Auto Spread
            'auto_spread_ids': [
                (0, 0, {'account_id': self.invoice_account.id})]
        })
        template2._check_auto_spread_ids_unique()

        self.assertFalse(self.invoice_line.spread_id)
        with self.assertRaises(UserError):  # too many auto_spread_ids matched
            self.invoice.action_invoice_open()

        template2.auto_spread = False  # Do not use this template
        self.invoice.action_invoice_open()
        self.assertTrue(self.invoice_line.spread_id)

        spread_lines = self.invoice_line.spread_id.line_ids
        self.assertTrue(spread_lines)

        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

    def test_03_new_auto_spread_sheet_sale(self):

        self.env['account.spread.template'].create({
            'name': 'test',
            'spread_type': 'sale',
            'period_number': 5,
            'period_type': 'month',
            'spread_account_id': self.account_revenue.id,
            'spread_journal_id': self.ref(
                'account_spread_cost_revenue.sales_journal'),
            'auto_spread': True,  # Auto Spread
            'auto_spread_ids': [(0, 0, {'account_id': self.invoice_line_account.id})]
        })

        self.assertFalse(self.invoice_line_2.spread_id)
        self.invoice_2.action_invoice_open()
        self.assertTrue(self.invoice_line_2.spread_id)

        spread_lines = self.invoice_line_2.spread_id.line_ids
        self.assertTrue(spread_lines)

        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)
