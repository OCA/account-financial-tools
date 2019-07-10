# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import SavepointCase, Form
from odoo import tools
from odoo.modules.module import get_resource_path
from odoo.exceptions import ValidationError


class TestAssetSalvageValue(SavepointCase):

    @classmethod
    def _load(cls, module, *args):
        tools.convert_file(cls.cr, module,
                           get_resource_path(module, *args),
                           {}, 'init', False, 'test',
                           cls.registry._assertion_report)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._load('account', 'test', 'account_minimal_test.xml')
        cls._load('account_asset_management', 'tests',
                  'account_asset_test_data.xml')

        # ENVIRONEMENTS
        cls.asset_model = cls.env['account.asset']
        cls.account_invoice = cls.env['account.invoice']
        cls.account_account = cls.env['account.account']
        cls.account_journal = cls.env['account.journal']
        cls.account_invoice_line = cls.env['account.invoice.line']

        # INSTANCES

        # Instance: company
        cls.company = cls.env.ref('base.main_company')

        # Instance: account type (receivable)
        cls.type_recv = cls.env.ref('account.data_account_type_receivable')

        # Instance: account type (payable)
        cls.type_payable = cls.env.ref('account.data_account_type_payable')

        # Instance: account (receivable)
        cls.account_recv = cls.account_account.create({
            'name': 'test_account_receivable',
            'code': '123',
            'user_type_id': cls.type_recv.id,
            'company_id': cls.company.id,
            'reconcile': True})

        # Instance: account (payable)
        cls.account_payable = cls.account_account.create({
            'name': 'test_account_payable',
            'code': '321',
            'user_type_id': cls.type_payable.id,
            'company_id': cls.company.id,
            'reconcile': True})

        # Instance: partner
        cls.partner = cls.env.ref('base.res_partner_2')

        # Instance: journal
        cls.journal = cls.account_journal.search(
            [('type', '=', 'purchase')])[0]

        # Instance: product
        cls.product = cls.env.ref('product.product_product_4')

        # Instance: invoice
        cls.invoice_line_2 = cls.account_invoice_line.create({
            'name': 'test 2',
            'account_id': cls.account_payable.id,
            'price_unit': 10000.00,
            'quantity': 1,
            'product_id': cls.product.id})
        cls.invoice_line_3 = cls.account_invoice_line.create({
            'name': 'test 3',
            'account_id': cls.account_payable.id,
            'price_unit': 20000.00,
            'quantity': 1,
            'product_id': cls.product.id})

        cls.invoice_2 = cls.account_invoice.create({
            'partner_id': cls.partner.id,
            'account_id': cls.account_recv.id,
            'journal_id': cls.journal.id,
            'invoice_line_ids': [(4, cls.invoice_line_2.id),
                                 (4, cls.invoice_line_3.id)]})

    def update_salvage_value_wizard(self, asset, amount):
        res = asset.button_edit_salvage()
        ctx = {'active_model': 'account.asset',
               'active_ids': [asset.id]}
        f = Form(self.env[res['res_model']].with_context(ctx))
        f.salvage_value = amount
        update_salvage_value = f.save()
        update = update_salvage_value.action_confirm()
        return update

    def test_1_assets_from_invoice(self):
        all_assets = self.env['account.asset'].search([])
        invoice = self.invoice_2
        asset_profile = self.env.ref(
            'account_asset_management.account_asset_profile_car_5Y')
        asset_profile.asset_product_item = True
        # Compute depreciation lines on invoice validation
        asset_profile.open_asset = True

        self.assertTrue(len(invoice.invoice_line_ids) == 2)
        invoice.invoice_line_ids.write({
            'quantity': 1,
            'asset_profile_id': asset_profile.id,
        })
        invoice.action_invoice_open()
        # Retrieve all assets after invoice validation
        current_assets = self.env['account.asset'].search([])
        # What are the new assets?
        new_assets = current_assets - all_assets
        self.assertEqual(len(new_assets), 2)

        for asset in new_assets:
            asset.purchase_value = abs(asset.purchase_value)
            with self.assertRaises(ValidationError):
                self.update_salvage_value_wizard(
                    asset, asset.purchase_value+100.0)
            with self.assertRaises(ValidationError):
                self.update_salvage_value_wizard(asset, -100.0)
            self.update_salvage_value_wizard(asset, 100.0)
            self.assertAlmostEqual(asset.salvage_value, 100.0)
            self.assertAlmostEqual(
                asset.depreciation_base, asset.purchase_value-100.0)
            asset.compute_depreciation_board()
            dlines = asset.depreciation_line_ids.filtered(
                lambda l: l.type == 'depreciate')
            dlines = dlines.sorted(key=lambda l: l.line_date)
            self.assertAlmostEqual(dlines[0].depreciated_value, 0.0)
            self.assertAlmostEqual(dlines[-1].remaining_value, 0.0)
