# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestAccountAssetMaintenance(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountAssetMaintenance, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test partner',
        })
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'general',
            'update_posted': True,
        })
        cls.account_type = cls.env['account.account.type'].create({
            'name': 'Test account type',
            'type': 'other',
        })
        cls.account = cls.env['account.account'].create({
            'name': 'Test account',
            'code': 'TEST',
            'user_type_id': cls.account_type.id,
        })
        cls.equipment_category = cls.env[
            'maintenance.equipment.category'
        ].create({
            'name': 'Test equipment category',
        })
        cls.asset_category = cls.env['account.asset.category'].create({
            'name': 'Test assset category',
            'journal_id': cls.journal.id,
            'account_asset_id': cls.account.id,
            'account_depreciation_expense_id': cls.account.id,
            'account_depreciation_id': cls.account.id,
            'equipment_category_id': cls.equipment_category.id,
        })
        cls.invoice = cls.env['account.invoice'].create({
            'partner_id': cls.partner.id,
            'journal_id': cls.journal.id,
            'type': 'in_invoice',
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Test line',
                    'asset_category_id': cls.asset_category.id,
                    'quantity': 1,
                    'price_unit': 50,
                    'account_id': cls.account.id,
                })
            ]
        })
        cls.invoice_line = cls.invoice.invoice_line_ids[0]

    def test_flow(self):
        # HACK: There's no way to the created asset
        prev_assets = self.env['account.asset.asset'].search([])
        self.invoice.action_invoice_open()
        current_assets = self.env['account.asset.asset'].search([])
        asset = current_assets - prev_assets
        self.assertEqual(len(asset.equipment_ids), 1)
        res = asset.button_open_equipment()
        self.assertEqual(res['domain'], [('asset_ids', 'in', asset.ids)])
        self.assertEqual(len(self.invoice_line.equipment_ids), 1)
        self.assertEqual(len(self.invoice.equipment_ids), 1)
        equipment = self.invoice_line.equipment_ids
        self.assertEqual(equipment.name, 'Test line [1/1]')
        self.assertEqual(equipment.cost, 50)
        self.assertEqual(equipment.category_id, self.equipment_category)
        self.invoice.action_invoice_cancel()
        self.assertFalse(self.invoice_line.equipment_ids)

    def test_multi(self):
        self.invoice_line.quantity = 3
        self.invoice.action_invoice_open()
        self.assertEqual(len(self.invoice_line.equipment_ids), 3)
        equipments = self.invoice_line.equipment_ids
        for i in range(1, 4):
            self.assertTrue(equipments.filtered(
                lambda x: x.name == 'Test line [{}/3]'.format(i)
            ))
