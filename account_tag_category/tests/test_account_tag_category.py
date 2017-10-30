# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestAccountTagCategory(TransactionCase):

    def setUp(self):
        super(TestAccountTagCategory, self).setUp()

        # Create a few tags
        self.tag_model = self.env['account.account.tag'].with_context(
            default_applicability='accounts')
        category_model = self.env[
            'account.account.tag.category'].with_context(
            default_applicability='accounts')

        tags_to_create = ['123', '456', '789', 'ABC', 'DEF', 'GHI']

        for tag_name in tags_to_create:
            self.tag_model.create({
                'name': tag_name,
            })

        self.letters_category = category_model.create({
            'name': 'Letters',
            'enforce_policy': 'required',
            'color_picker': '1',
        })
        self.numbers_category = category_model.create({
            'name': 'Numbers',
            'enforce_policy': 'optional',
            'color_picker': '2',
        })

        update_wizard = self.env['account.tag.category.update.tags']

        update_wizard.create({
            'tag_category_id': self.letters_category.id,
            'tag_ids': [(6, False, self.tag_model.search(
                ['|', '|', ('name', '=', 'ABC'), ('name', '=', 'DEF'),
                 ('name', '=', 'GHI')]).ids)],
        }).save_tags_to_category()

        update_wizard.create({
            'tag_category_id': self.numbers_category.id,
            'tag_ids': [(6, False, self.tag_model.search(
                ['|', '|', ('name', '=', '123'), ('name', '=', '456'),
                 ('name', '=', '789')]).ids)],
        }).save_tags_to_category()

    def test_categories(self):

        self.assertEqual(self.letters_category.color,
                         int(self.letters_category.color_picker))

        self.tag_model.invalidate_cache()

        tag_color = self.tag_model.search([('name', '=', 'ABC')]).read(
            ['color'])[0]['color']

        self.assertEqual(tag_color, self.letters_category.color)

        self.assertEqual(len(self.letters_category.tag_ids), 3)

        # Missing required category
        with self.assertRaises(ValidationError):
            self.env['account.account'].create({
                'name': "Dummy account",
                'code': "DUMMY",
                'user_type_id': self.env.ref(
                    'account.data_account_type_equity').id,
            })

        with self.assertRaises(ValidationError):
            self.env['account.account'].create({
                'name': "Dummy account",
                'code': "DUMMY 2",
                'user_type_id': self.env.ref(
                    'account.data_account_type_equity').id,
                'tag_ids': [(6, False, self.tag_model.search(
                    [('name', '=', '123')]).ids)]
            })

        # Two times same category
        with self.assertRaises(ValidationError):
            self.env['account.account'].create({
                'name': "Dummy account",
                'code': "DUMMY 3",
                'user_type_id': self.env.ref(
                    'account.data_account_type_equity').id,
                'tag_ids': [(6, False,
                             self.tag_model.search(
                                 ['|', ('name', '=', 'ABC'),
                                  ('name', '=', 'DEF')]).ids)]
            })

        self.env['account.account'].create({
            'name': "Dummy account",
            'code': "DUMMY 4",
            'user_type_id': self.env.ref(
                'account.data_account_type_equity').id,
            'tag_ids': [(6, False,
                         self.tag_model.search(
                             ['|', ('name', '=', '123'),
                              ('name', '=', 'DEF')]).ids)]
        })

    def test_wizard(self):

        wiz = self.env['account.tag.category.update.tags'].with_context(
            default_tag_category_id=self.letters_category.id).create({})

        self.assertEqual(wiz.tag_ids, self.letters_category.tag_ids)

        tag_123 = self.env['account.account.tag'].search(
            [('name', '=', '123')])
        wiz.write({
            'tag_ids': [(4, tag_123.id, False)]
        })
        with self.assertRaises(ValidationError):
            wiz.save_tags_to_category()

        self.assertEqual(len(self.letters_category.tag_ids), 3)

        wiz.write({
            'tag_ids': [(3, tag_123.id, False), (0, False, {'name': 'JKL'})]
        })
        wiz.save_tags_to_category()

        self.assertEqual(len(self.letters_category.tag_ids), 4)
