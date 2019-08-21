# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo.tools import convert_file
from odoo.modules.module import get_resource_path
from odoo.exceptions import UserError, ValidationError
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

        analytic_tags = [(6, 0, self.env.ref('analytic.tag_contract').ids)]
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'test account',
        })
        self.spread = self.env['account.spread'].with_context(
            mail_create_nosubscribe=True
        ).create([{
            'name': 'test',
            'debit_account_id': self.spread_account.id,
            'credit_account_id': self.invoice_line_account.id,
            'period_number': 12,
            'period_type': 'month',
            'spread_date': datetime.date(2017, 2, 1),
            'estimated_amount': 1000.0,
            'journal_id': self.invoice.journal_id.id,
            'invoice_type': 'in_invoice',
            'account_analytic_id': self.analytic_account.id,
            'analytic_tag_ids': analytic_tags,
        }])

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
        self.spread2 = self.env['account.spread'].create([{
            'name': 'test2',
            'debit_account_id': self.spread_account.id,
            'credit_account_id': self.invoice_line_account.id,
            'period_number': 12,
            'period_type': 'month',
            'spread_date': datetime.date(2017, 2, 1),
            'estimated_amount': 1000.0,
            'journal_id': self.invoice_2.journal_id.id,
            'invoice_type': 'out_invoice',
        }])

    def test_01_wizard_defaults(self):
        my_company = self.env.user.company_id
        Wizard = self.env['account.spread.invoice.line.link.wizard']
        wizard1 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line.id,
            default_company_id=my_company.id,
            allow_spread_planning=True,
        ).create({})

        self.assertEqual(wizard1.invoice_line_id, self.invoice_line)
        self.assertEqual(wizard1.invoice_line_id.invoice_id, self.invoice)
        self.assertEqual(wizard1.invoice_type, 'in_invoice')
        self.assertFalse(wizard1.spread_id)
        self.assertEqual(wizard1.company_id, my_company)
        self.assertEqual(wizard1.spread_action_type, 'link')
        self.assertFalse(wizard1.spread_account_id)
        self.assertFalse(wizard1.spread_journal_id)

        wizard2 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line_2.id,
            default_company_id=my_company.id,
        ).create({})

        self.assertEqual(wizard2.invoice_line_id, self.invoice_line_2)
        self.assertEqual(wizard2.invoice_line_id.invoice_id, self.invoice_2)
        self.assertEqual(wizard2.invoice_type, 'out_invoice')
        self.assertFalse(wizard2.spread_id)
        self.assertEqual(wizard2.company_id, my_company)
        self.assertEqual(wizard2.spread_action_type, 'template')
        self.assertFalse(wizard2.spread_account_id)
        self.assertFalse(wizard2.spread_journal_id)

    def test_02_wizard_defaults(self):
        my_company = self.env.user.company_id
        Wizard = self.env['account.spread.invoice.line.link.wizard']

        account_revenue = self.account_revenue
        account_payable = self.account_payable
        exp_journal = self.ref('account_spread_cost_revenue.expenses_journal')
        sales_journal = self.ref('account_spread_cost_revenue.sales_journal')
        my_company.default_spread_revenue_account_id = account_revenue
        my_company.default_spread_expense_account_id = account_payable
        my_company.default_spread_revenue_journal_id = sales_journal
        my_company.default_spread_expense_journal_id = exp_journal

        self.assertTrue(my_company.default_spread_revenue_account_id)
        self.assertTrue(my_company.default_spread_expense_account_id)
        self.assertTrue(my_company.default_spread_revenue_journal_id)
        self.assertTrue(my_company.default_spread_expense_journal_id)

        wizard1 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line.id,
            default_company_id=my_company.id,
            allow_spread_planning=True,
        ).create({})

        self.assertEqual(wizard1.invoice_line_id, self.invoice_line)
        self.assertEqual(wizard1.invoice_line_id.invoice_id, self.invoice)
        self.assertEqual(wizard1.invoice_type, 'in_invoice')
        self.assertFalse(wizard1.spread_id)
        self.assertEqual(wizard1.company_id, my_company)
        self.assertEqual(wizard1.spread_action_type, 'link')
        self.assertFalse(wizard1.spread_account_id)
        self.assertFalse(wizard1.spread_journal_id)

        res_onchange = wizard1.onchange_invoice_type()
        self.assertTrue(res_onchange)
        self.assertTrue(res_onchange.get('domain'))

        wizard1._onchange_spread_journal_account()
        self.assertTrue(wizard1.spread_account_id)
        self.assertTrue(wizard1.spread_journal_id)
        self.assertEqual(wizard1.spread_account_id, account_payable)
        self.assertEqual(wizard1.spread_journal_id.id, exp_journal)

        wizard2 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line_2.id,
            default_company_id=my_company.id,
        ).create({})

        self.assertEqual(wizard2.invoice_line_id, self.invoice_line_2)
        self.assertEqual(wizard2.invoice_line_id.invoice_id, self.invoice_2)
        self.assertEqual(wizard2.invoice_type, 'out_invoice')
        self.assertFalse(wizard2.spread_id)
        self.assertEqual(wizard2.company_id, my_company)
        self.assertEqual(wizard2.spread_action_type, 'template')
        self.assertFalse(wizard2.spread_account_id)
        self.assertFalse(wizard2.spread_journal_id)

        res_onchange = wizard2.onchange_invoice_type()
        self.assertTrue(res_onchange)
        self.assertTrue(res_onchange.get('domain'))

        wizard2._onchange_spread_journal_account()
        self.assertTrue(wizard2.spread_account_id)
        self.assertTrue(wizard2.spread_journal_id)
        self.assertEqual(wizard2.spread_account_id, account_revenue)
        self.assertEqual(wizard2.spread_journal_id.id, sales_journal)

    def test_03_link_invoice_line_with_spread_sheet(self):

        my_company = self.env.user.company_id
        Wizard = self.env['account.spread.invoice.line.link.wizard']
        wizard1 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line.id,
            default_company_id=my_company.id,
            allow_spread_planning=True,
        ).create({})
        self.assertEqual(wizard1.spread_action_type, 'link')

        wizard1.spread_account_id = self.account_revenue
        wizard1.spread_journal_id = self.ref(
            'account_spread_cost_revenue.expenses_journal')
        wizard1.spread_id = self.spread
        res_action = wizard1.confirm()
        self.assertTrue(isinstance(res_action, dict))
        self.assertTrue(res_action.get('res_id'))
        self.assertEqual(res_action.get('res_id'), self.spread.id)
        self.assertTrue(self.spread.invoice_line_id)
        self.assertEqual(self.spread.invoice_line_id, self.invoice_line)

        spread_lines = self.spread.line_ids
        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.invoice.journal_id.update_posted = True

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)
            self.assertTrue(line.move_id.journal_id.update_posted)
            for ml in line.move_id.line_ids:
                ml_analytic_account = ml.analytic_account_id
                analytic_tag = self.env.ref('analytic.tag_contract')
                self.assertEqual(ml_analytic_account, self.analytic_account)
                self.assertEqual(ml.analytic_tag_ids, analytic_tag)

        self.spread.invoice_id.action_cancel()

        self.assertTrue(self.spread.invoice_line_id)
        with self.assertRaises(UserError):
            self.spread.unlink()
        with self.assertRaises(UserError):
            self.spread.action_unlink_invoice_line()
        self.assertTrue(self.spread.invoice_line_id)

    def test_04_new_spread_sheet(self):

        my_company = self.env.user.company_id
        Wizard = self.env['account.spread.invoice.line.link.wizard']

        spread_account = self.account_revenue
        spread_journal_id = self.ref(
            'account_spread_cost_revenue.expenses_journal')

        wizard1 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line.id,
            default_company_id=my_company.id,
        ).create({
            'spread_action_type': 'new',
        })
        self.assertEqual(wizard1.spread_action_type, 'new')

        wizard1.write({
            'spread_account_id': spread_account.id,
            'spread_journal_id': spread_journal_id,
        })

        res_action = wizard1.confirm()
        self.assertTrue(isinstance(res_action, dict))
        self.assertFalse(res_action.get('res_id'))
        self.assertTrue(res_action.get('context'))
        res_context = res_action.get('context')
        self.assertTrue(res_context.get('default_name'))
        self.assertTrue(res_context.get('default_invoice_type'))
        self.assertTrue(res_context.get('default_invoice_line_id'))
        self.assertTrue(res_context.get('default_debit_account_id'))
        self.assertTrue(res_context.get('default_credit_account_id'))

        spread_lines = self.spread.line_ids
        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        wizard2 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line_2.id,
            default_company_id=my_company.id,
        ).create({
            'spread_action_type': 'new',
        })
        self.assertEqual(wizard2.spread_action_type, 'new')

        wizard2.write({
            'spread_account_id': spread_account.id,
            'spread_journal_id': spread_journal_id,
        })

        res_action = wizard2.confirm()
        self.assertTrue(isinstance(res_action, dict))
        self.assertFalse(res_action.get('res_id'))
        self.assertTrue(res_action.get('context'))
        res_context = res_action.get('context')
        self.assertTrue(res_context.get('default_name'))
        self.assertTrue(res_context.get('default_invoice_type'))
        self.assertTrue(res_context.get('default_invoice_line_id'))
        self.assertTrue(res_context.get('default_debit_account_id'))
        self.assertTrue(res_context.get('default_credit_account_id'))

        spread_lines = self.spread2.line_ids
        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.spread2.compute_spread_board()
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

    def test_05_new_spread_sheet_from_template(self):

        my_company = self.env.user.company_id
        Wizard = self.env['account.spread.invoice.line.link.wizard']

        spread_account = self.account_payable
        self.assertTrue(spread_account)
        spread_journal_id = self.ref(
            'account_spread_cost_revenue.expenses_journal')

        template = self.env['account.spread.template'].create({
            'name': 'test',
            'spread_type': 'purchase',
            'period_number': 5,
            'period_type': 'month',
            'spread_account_id': spread_account.id,
            'spread_journal_id': spread_journal_id,
        })

        wizard1 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line.id,
            default_company_id=my_company.id,
        ).create({
            'spread_action_type': 'template',
            'template_id': template.id,
        })
        self.assertEqual(wizard1.spread_action_type, 'template')

        res_action = wizard1.confirm()
        self.assertTrue(isinstance(res_action, dict))
        self.assertTrue(res_action.get('res_id'))

        spread_lines = self.spread.line_ids
        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        wizard2 = Wizard.with_context(
            default_invoice_line_id=self.invoice_line_2.id,
            default_company_id=my_company.id,
        ).create({
            'spread_action_type': 'new',
        })
        self.assertEqual(wizard2.spread_action_type, 'new')

        wizard2.write({
            'spread_account_id': spread_account.id,
            'spread_journal_id': spread_journal_id,
        })

        res_action = wizard2.confirm()
        self.assertTrue(isinstance(res_action, dict))
        self.assertFalse(res_action.get('res_id'))
        self.assertTrue(res_action.get('context'))
        res_context = res_action.get('context')
        self.assertTrue(res_context.get('default_name'))
        self.assertTrue(res_context.get('default_invoice_type'))
        self.assertTrue(res_context.get('default_invoice_line_id'))
        self.assertTrue(res_context.get('default_debit_account_id'))
        self.assertTrue(res_context.get('default_credit_account_id'))

        spread_lines = self.spread2.line_ids
        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.spread2.compute_spread_board()
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

    def test_06_open_wizard(self):

        res_action = self.invoice_line.spread_details()
        self.assertTrue(isinstance(res_action, dict))
        self.assertFalse(res_action.get('res_id'))
        self.assertTrue(res_action.get('context'))

    def test_07_unlink_invoice_line_and_spread_sheet(self):

        self.assertFalse(self.spread.invoice_line_id)
        self.invoice_line.spread_id = self.spread
        self.assertTrue(self.spread.invoice_line_id)
        self.spread.action_unlink_invoice_line()
        self.assertFalse(self.spread.invoice_line_id)

        self.assertFalse(self.spread2.invoice_line_id)
        self.invoice_line_2.spread_id = self.spread2
        self.assertTrue(self.spread2.invoice_line_id)
        self.spread2.action_unlink_invoice_line()
        self.assertFalse(self.spread2.invoice_line_id)

    def test_08_invoice_multi_line(self):
        self.invoice_line.copy()
        self.assertEqual(len(self.invoice.invoice_line_ids), 2)

        self.invoice.invoice_line_ids[0].spread_id = self.spread
        self.assertTrue(self.spread.invoice_line_id)
        self.assertEqual(self.spread.invoice_line_id, self.invoice_line)

        spread_lines = self.spread.line_ids
        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        # Validate invoice
        self.invoice.action_invoice_open()

    def test_09_no_link_invoice(self):

        balance_sheet = self.spread.credit_account_id

        # Validate invoice
        self.invoice.action_invoice_open()

        invoice_mls = self.invoice.move_id.mapped('line_ids')
        self.assertTrue(invoice_mls)
        for invoice_ml in invoice_mls:
            if invoice_ml.debit:
                self.assertNotEqual(invoice_ml.account_id, balance_sheet)

    def test_10_link_vendor_bill_line_with_spread_sheet(self):

        copied_line = self.invoice_line.copy()
        copied_line.name = 'new test line'
        self.spread.write({
            'estimated_amount': 1000.0,
            'period_number': 12,
            'period_type': 'month',
            'spread_date': datetime.date(2017, 1, 7),
            'invoice_line_id': self.invoice_line.id,
            'move_line_auto_post': False,
        })

        spread_lines = self.spread.line_ids
        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        expense_account = self.spread.debit_account_id
        balance_sheet = self.spread.credit_account_id
        self.assertTrue(balance_sheet.reconcile)

        spread_mls = self.spread.line_ids.mapped('move_id.line_ids')
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertEqual(spread_ml.account_id, expense_account)
            if spread_ml.credit:
                self.assertEqual(spread_ml.account_id, balance_sheet)

        # Validate invoice
        self.invoice.action_invoice_open()

        invoice_mls = self.invoice.move_id.mapped('line_ids')
        self.assertTrue(invoice_mls)

        count_balance_sheet = len(invoice_mls.filtered(
            lambda x: x.account_id == balance_sheet))
        self.assertEqual(count_balance_sheet, 1)

        self.spread.line_ids.create_and_reconcile_moves()

        spread_mls = self.spread.line_ids.mapped('move_id.line_ids')
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertFalse(spread_ml.full_reconcile_id)
            if spread_ml.credit:
                self.assertTrue(spread_ml.full_reconcile_id)

        action_reconcile_view = self.spread2.open_reconcile_view()
        self.assertTrue(isinstance(action_reconcile_view, dict))
        self.assertFalse(action_reconcile_view.get('domain')[0][2])
        self.assertTrue(action_reconcile_view.get('context'))

    def test_11_link_vendor_bill_line_with_spread_sheet(self):
        self.invoice_line.copy()
        self.spread.write({
            'estimated_amount': 1000.0,
            'period_number': 12,
            'period_type': 'month',
            'spread_date': datetime.date(2017, 1, 7),
            'invoice_line_id': self.invoice_line.id,
            'move_line_auto_post': False,
        })

        spread_lines = self.spread.line_ids
        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        expense_account = self.spread.debit_account_id
        balance_sheet = self.spread.credit_account_id
        self.assertTrue(balance_sheet.reconcile)

        spread_mls = self.spread.line_ids.mapped('move_id.line_ids')
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertEqual(spread_ml.account_id, expense_account)
            if spread_ml.credit:
                self.assertEqual(spread_ml.account_id, balance_sheet)

        # Validate invoice
        self.invoice.action_invoice_open()

        invoice_mls = self.invoice.move_id.mapped('line_ids')
        self.assertTrue(invoice_mls)

        count_balance_sheet = len(invoice_mls.filtered(
            lambda x: x.account_id == balance_sheet))
        self.assertEqual(count_balance_sheet, 1)

        self.spread.company_id.force_move_auto_post = True
        self.spread.line_ids.create_and_reconcile_moves()

        spread_mls = self.spread.line_ids.mapped('move_id.line_ids')
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            self.assertFalse(spread_ml.full_reconcile_id)

        action_reconcile_view = self.spread.open_reconcile_view()
        self.assertTrue(isinstance(action_reconcile_view, dict))
        self.assertTrue(action_reconcile_view.get('domain')[0][2])
        self.assertTrue(action_reconcile_view.get('context'))

        action_spread_details = self.invoice_line.spread_details()
        self.assertTrue(isinstance(action_spread_details, dict))
        self.assertTrue(action_spread_details.get('res_id'))

    def test_12_link_invoice_line_with_spread_sheet_full_reconcile(self):

        self.spread2.write({
            'estimated_amount': 1000.0,
            'period_number': 12,
            'period_type': 'month',
            'spread_date': datetime.date(2017, 1, 7),
            'invoice_line_id': self.invoice_line_2.id,
            'move_line_auto_post': False,
        })

        spread_lines = self.spread2.line_ids
        for line in spread_lines:
            self.assertFalse(line.move_id)

        self.spread2.compute_spread_board()
        spread_lines = self.spread2.line_ids
        for line in spread_lines:
            line.create_move()
            self.assertTrue(line.move_id)

        payable_account = self.spread.credit_account_id
        balance_sheet = self.spread.debit_account_id
        self.assertTrue(balance_sheet.reconcile)

        spread_mls = self.spread2.line_ids.mapped('move_id.line_ids')
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertEqual(spread_ml.account_id, balance_sheet)
            if spread_ml.credit:
                self.assertEqual(spread_ml.account_id, payable_account)

        # Validate invoice
        self.invoice_2.action_invoice_open()

        invoice_mls = self.invoice_2.move_id.mapped('line_ids')
        self.assertTrue(invoice_mls)
        for invoice_ml in invoice_mls:
            if invoice_ml.credit:
                self.assertEqual(invoice_ml.account_id, balance_sheet)

        self.spread2.line_ids.create_and_reconcile_moves()

        spread_mls = self.spread2.line_ids.mapped('move_id.line_ids')
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertTrue(spread_ml.full_reconcile_id)
            if spread_ml.credit:
                self.assertFalse(spread_ml.full_reconcile_id)

        action_reconcile_view = self.spread2.open_reconcile_view()
        self.assertTrue(isinstance(action_reconcile_view, dict))
        self.assertTrue(action_reconcile_view.get('domain')[0][2])
        self.assertFalse(action_reconcile_view.get('res_id'))
        self.assertTrue(action_reconcile_view.get('context'))

        action_spread_details = self.invoice_line_2.spread_details()
        self.assertTrue(isinstance(action_spread_details, dict))
        self.assertTrue(action_spread_details.get('res_id'))

    def test_13_link_invoice_line_with_spread_sheet_partial_reconcile(self):

        self.spread2.write({
            'estimated_amount': 1000.0,
            'period_number': 12,
            'period_type': 'month',
            'spread_date': datetime.date(2017, 1, 7),
        })

        self.spread2.compute_spread_board()
        spread_lines = self.spread2.line_ids
        self.assertEqual(len(spread_lines), 13)

        for line in spread_lines:
            self.assertFalse(line.move_id)

        spread_lines[0]._create_moves().post()
        spread_lines[1]._create_moves().post()
        spread_lines[2]._create_moves().post()
        spread_lines[3]._create_moves().post()

        self.assertEqual(spread_lines[0].move_id.state, 'posted')
        self.assertEqual(spread_lines[1].move_id.state, 'posted')
        self.assertEqual(spread_lines[2].move_id.state, 'posted')
        self.assertEqual(spread_lines[3].move_id.state, 'posted')

        spread_mls = spread_lines[0].move_id.line_ids
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertFalse(spread_ml.matched_debit_ids)
                self.assertFalse(spread_ml.matched_credit_ids)
                self.assertFalse(spread_ml.full_reconcile_id)
            if spread_ml.credit:
                self.assertFalse(spread_ml.matched_debit_ids)
                self.assertFalse(spread_ml.matched_credit_ids)
                self.assertFalse(spread_ml.full_reconcile_id)

        balance_sheet = self.spread.debit_account_id
        self.assertTrue(balance_sheet.reconcile)

        self.spread2.write({
            'invoice_line_id': self.invoice_line_2.id,
        })

        # Validate invoice
        self.invoice_2.action_invoice_open()

        invoice_mls = self.invoice_2.move_id.mapped('line_ids')
        self.assertTrue(invoice_mls)
        for invoice_ml in invoice_mls:
            if invoice_ml.credit:
                self.assertEqual(invoice_ml.account_id, balance_sheet)

        spread_mls = spread_lines[0].move_id.line_ids
        self.assertTrue(spread_mls)
        for spread_ml in spread_mls:
            if spread_ml.debit:
                self.assertFalse(spread_ml.matched_debit_ids)
                self.assertTrue(spread_ml.matched_credit_ids)
                self.assertFalse(spread_ml.full_reconcile_id)
            if spread_ml.credit:
                self.assertFalse(spread_ml.matched_debit_ids)
                self.assertFalse(spread_ml.matched_credit_ids)
                self.assertFalse(spread_ml.full_reconcile_id)

        other_journal = self.env['account.journal'].create({
            'name': 'Other Journal', 'type': 'general', 'code': 'test2'})
        with self.assertRaises(ValidationError):
            self.spread2.journal_id = other_journal

        with self.assertRaises(UserError):
            self.spread2.unlink()

    def test_14_create_all_moves(self):
        self.spread.compute_spread_board()
        spread_lines = self.spread.line_ids
        self.assertEqual(len(spread_lines), 12)
        for line in spread_lines:
            self.assertFalse(line.move_id)

        # create moves for all the spread lines
        self.spread.create_all_moves()
        spread_lines = self.spread.line_ids
        for line in spread_lines:
            self.assertTrue(line.move_id)

        with self.assertRaises(ValidationError):
            self.spread.unlink()

    def test_15_invoice_refund(self):

        self.invoice_line.spread_id = self.spread

        # Validate invoice
        self.invoice.action_invoice_open()
        self.assertTrue(self.invoice.invoice_line_ids.mapped('spread_id'))

        # Create a refund for invoice.
        self.env['account.invoice.refund'].with_context({
            'active_model': 'account.invoice',
            'active_ids': [self.invoice.id],
            'active_id': self.invoice.id
        }).create(dict(
            description='Invoice Refund',
            filter_refund='refund',
        )).invoice_refund()

        # Invoice lines do not contain the lint to the spread.
        refund = self.invoice.refund_invoice_ids[0]
        self.assertFalse(refund.invoice_line_ids.mapped('spread_id'))
