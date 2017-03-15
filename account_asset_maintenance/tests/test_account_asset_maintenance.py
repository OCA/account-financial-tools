# -*- coding: utf-8 -*-
# Copyright 2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import common


class TestAccountAssetMaintenance(common.TransactionCase):

    def setUp(self):
        super(TestAccountAssetMaintenance, self).setUp()
        self.Asset = self.env['account.asset.asset']
        self.AssetCategory = self.env['account.asset.category']
        self.Journal = self.env['account.journal']
        self.Equipment = self.env['maintenance.equipment']
        self.Template = self.env['mail.template']
        self.Wizard = self.env['wizard.perform.equipment.scrap']

        acc_asset = self.env.ref('account.data_account_type_current_assets')
        acc_exp = self.env.ref('account.data_account_type_expenses')
        acc_depr = self.env.ref('account.data_account_type_depreciation')

        self.template = self.Template.create({
            'name': 'Template 1',
            'email_from': 'info@openerp.com',
            'subject': 'Template Test',
            'email_to': '',
            'model_id': self.env.ref(
                'maintenance.model_maintenance_equipment').id,
        })

        self.journal_1 = self.Journal.create({
            'name': 'Journal 1',
            'code': 'Jou1',
            'type': 'sale',
        })

        self.asset_category = self.AssetCategory.create({
            'name': 'Category 1',
            'journal_id': self.journal_1.id,
            'account_asset_id': acc_asset.id,
            'account_depreciation_id': acc_depr.id,
            'account_depreciation_expense_id': acc_exp.id,
        })

        self.asset1 = self.Asset.create({
            'name': 'Asset 1',
            'category_id': self.asset_category.id,
            'value': 1000.0,
        })

        self.asset2 = self.Asset.with_context(
            default_type='in_invoice').create({
                'name': 'Asset 1',
                'category_id': self.asset_category.id,
                'value': 1000.0,
            })

        self.equipment1 = self.Equipment.create({
            'name': 'Equipment 1',
            'equipment_scrap_template_id': self.template.id,
        })

        self.equipment2 = self.Equipment.create({
            'name': 'Equipment 2',
        })

    def test_01_asset_write(self):
        self.asset1.write({'equipment_id': self.equipment1.id})
        self.asset2.with_context(default_type='in_invoice').write(
            {'equipment_id': self.equipment2.id})

    def test_02_equipment_write(self):
        self.equipment1.write({'asset_id': self.asset1.id})
        self.equipment2.with_context(default_type='in_invoice').write(
            {'asset_id': self.asset2.id})

    def test_03_asset_create(self):
        self.Asset.create({
            'name': 'Asset 1',
            'category_id': self.asset_category.id,
            'value': 1000.0,
            'equipment_id': self.equipment1.id,
        })

    def test_04_equipment_create(self):
        self.Equipment.create({
            'name': 'Equipment 1',
            'asset_id': self.asset1.id,
        })

    def test_05_wizard(self):
        wizard = self.Wizard.create({
            'scrap_date': fields.Date.today(),
            'equipment_id': self.equipment1.id,
        })
        wizard.do_scrap()

        self.equipment2.action_perform_scrap()
