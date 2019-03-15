# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import convert_file
from odoo.modules.module import get_module_resource
from odoo.addons.contract.tests.test_contract import TestContractBase


class TestAccountSpreadContract(TestContractBase):

    def _load(self, module, *args):
        convert_file(
            self.cr,
            'account_spread_contract',
            get_module_resource(module, *args),
            {}, 'init', False, 'test', self.registry._assertion_report)

    def setUp(self):
        super().setUp()
        self._load('account', 'test', 'account_minimal_test.xml')

        self.contract.recurring_next_date = '2016-02-29'
        self.contract.recurring_invoicing_type = 'pre-paid'
        self.contract.recurring_rule_type = 'monthly'

        self.receivable_account = self.env['account.account'].search([(
            'user_type_id',
            '=',
            self.env.ref('account.data_account_type_receivable').id)],
            limit=1)
        self.sales_journal_journal_id = self.ref(
            'account_spread_contract.sales_journal')

        self.sale_template = self.env['account.spread.template'].create({
            'name': 'test',
            'spread_type': 'sale',
            'spread_account_id': self.receivable_account.id,
            'spread_journal_id': self.sales_journal_journal_id,
        })

    def test_01_create_recurring_invoice_with_spread(self):
        self.assertTrue(self.receivable_account)

        self.assertEqual(len(self.contract.recurring_invoice_line_ids), 1)
        contract_line = self.contract.recurring_invoice_line_ids
        self.assertEqual(contract_line.spread_check, 'unlinked')

        contract_line.spread_template_id = self.sale_template
        self.assertEqual(contract_line.spread_check, 'linked')

        self.contract.recurring_create_invoice()
        invoice_monthly = self.env['account.invoice'].search(
            [('contract_id', '=', self.contract.id)])
        self.assertEqual(len(invoice_monthly), 1)

        self.assertEqual(len(invoice_monthly.invoice_line_ids), 1)
        spread = invoice_monthly.invoice_line_ids.spread_id
        self.assertTrue(spread)
        self.assertEqual(spread.template_id, self.sale_template)
        self.assertEqual(contract_line.spread_template_id, self.sale_template)

    def test_02_open_wizard(self):

        contract_line = self.contract.recurring_invoice_line_ids

        res_action = contract_line.spread_details()
        self.assertTrue(isinstance(res_action, dict))
        self.assertFalse(res_action.get('res_id'))
        self.assertTrue(res_action.get('context'))

        contract_line.spread_template_id = self.sale_template

        res_action = contract_line.spread_details()
        self.assertTrue(isinstance(res_action, dict))
        self.assertTrue(res_action.get('res_id'))
        self.assertTrue(res_action.get('context'))

    def test_03_wizard_create(self):
        my_company = self.env.user.company_id
        contract_line = self.contract.recurring_invoice_line_ids
        self.assertFalse(contract_line.spread_template_id)

        Wizard = self.env['account.spread.contract.line.link.wizard']
        wizard = Wizard.with_context(
            default_contract_line_id=contract_line.id,
            default_company_id=my_company.id,
        ).create({
            'spread_template_id': self.sale_template.id,
        })

        self.assertEqual(wizard.contract_line_id, contract_line)
        self.assertEqual(wizard.contract_id, self.contract)
        self.assertEqual(wizard.contract_type, 'sale')
        self.assertEqual(wizard.spread_template_id, self.sale_template)
        self.assertEqual(wizard.company_id, my_company)
        self.assertEqual(contract_line.spread_check, 'unlinked')

        wizard.confirm()
        self.assertEqual(contract_line.spread_template_id, self.sale_template)
        self.assertEqual(contract_line.spread_check, 'linked')

        ctx = {'force_contract_line_id': contract_line.id}
        self.sale_template.with_context(ctx).action_unlink_contract_line()
        self.assertFalse(contract_line.spread_template_id)
        self.assertEqual(contract_line.spread_check, 'unlinked')
