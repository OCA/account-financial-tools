# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class TestAccountAsset(TransactionCase):
    def setUp(self):
        super(TestAccountAsset, self).setUp()
        # Create a payable account for suppliers
        self.account_suppliers = self.env['account.account'].create({
            'name': 'Suppliers',
            'code': '410000',
            'type': 'other',
            'user_type': self.env.ref('account.data_account_type_payable').id,
            'reconcile': True,
        })
        # Create a supplier
        self.supplier = self.env['res.partner'].create({
            'name': 'Asset provider',
            'supplier': True,
            'customer': False,
        })
        # Create a journal for purchases
        self.journal_purchase = self.env['account.journal'].create({
            'name': 'Purchase journal',
            'code': 'PRCH',
            'type': 'purchase',
        })
        # Create a journal for assets
        self.journal_asset = self.env['account.journal'].create({
            'name': 'Asset journal',
            'code': 'JRNL',
            'type': 'general',
        })
        # Create an account for assets
        self.account_asset = self.env['account.account'].create({
            'name': 'Asset',
            'code': '216000',
            'type': 'other',
            'user_type': self.env.ref('account.data_account_type_asset').id,
            'reconcile': False,
        })
        # Create an account for assets dereciation
        self.account_asset_depreciation = self.env['account.account'].create({
            'name': 'Asset depreciation',
            'code': '281600',
            'type': 'other',
            'user_type': self.env.ref('account.data_account_type_asset').id,
            'reconcile': False,
        })
        # Create an account for assets expense
        self.account_asset_expense = self.env['account.account'].create({
            'name': 'Asset expense',
            'code': '681000',
            'type': 'other',
            'user_type': self.env.ref('account.data_account_type_expense').id,
            'reconcile': False,
        })
        # Create an account for assets loss
        self.account_asset_loss = self.env['account.account'].create({
            'name': 'Asset loss',
            'code': '671000',
            'type': 'other',
            'user_type': self.env.ref('account.data_account_type_expense').id,
            'reconcile': False,
        })
        # Create an assset category, with analytic account A
        self.asset_category = self.env['account.asset.category'].create({
            'name': 'Asset category for testing',
            'journal_id': self.journal_asset.id,
            'account_asset_id': self.account_asset.id,
            'account_depreciation_id': self.account_asset_depreciation.id,
            'account_expense_depreciation_id': self.account_asset_expense.id,
        })
        # Create an invoice
        self.asset_name = 'Office table'
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.supplier.id,
            'account_id': self.account_suppliers.id,
            'journal_id': self.journal_purchase.id,
            'reference_type': 'none',
            'reference': 'PURCHASE/12345',
            'invoice_line': [
                (0, False, {
                    'name': self.asset_name,
                    'account_id': self.account_asset.id,
                    'asset_category_id': self.asset_category.id,
                    'quantity': 1.0,
                    'price_unit': 100.00,
                }),
            ],
        })
        # Validate invoice
        self.invoice.signal_workflow('invoice_open')
        # Last period opened
        self.last_period = self.env['account.period'].search([
            ('state', '=', 'draft'),
            ('special', '=', False),
        ], limit=1, order='date_stop DESC')

    def test_asset_disposal(self):
        # Search asset created
        asset = self.env['account.asset.asset'].search([
            ('code', '=', self.invoice.number),
        ])
        # Asset must be created with code == invoice number
        self.assertTrue(asset)
        # Depreciate the first line
        line = asset.depreciation_line_ids.filtered(
            lambda x: x.move_check is False)[0]
        line.create_move()
        # Disposal asset
        disposal_date = self.last_period.date_stop
        wizard = self.env['account.asset.disposal.wizard'].with_context(
            active_ids=[asset.id]).create({
                'disposal_date': disposal_date,
                'loss_account_id': self.account_asset_loss.id,
            })
        wizard.action_disposal()
        # Disposal date
        self.assertEqual(disposal_date, asset.disposal_date)
        # Disposal move exists and posted
        self.assertTrue(asset.disposal_move_id)
        self.assertEqual('posted', asset.disposal_move_id.state)
        # Disposal move amount must be equal to asset purchase value
        self.assertEqual(asset.purchase_value, asset.disposal_move_id.amount)
