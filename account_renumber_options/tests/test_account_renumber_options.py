# -*- coding: utf-8 -*-
# Copyright 2017 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.tests import common
from openerp import fields, exceptions
from dateutil.relativedelta import relativedelta


class TestAccountRenumberOptions(common.TransactionCase):
    def setUp(self):
        super(TestAccountRenumberOptions, self).setUp()
        self.renumber_wiz_obj = self.env['wizard.renumber']
        self.config_obj = self.env['account.config.settings']
        acc_move_obj = self.env['account.move']
        journal = self.env.ref('account.expenses_journal')
        account = self.env.ref('account.cash')
        period1 = self.env.ref('account.period_1')
        period2 = self.env.ref('account.period_2')
        move_date = period1.date_start
        journal.sequence_id.write({'prefix': '', 'suffix': '', 'padding': 1})
        acc_lines = [
            (0, 0, {'account_id': account.id, 'credit': 1000, 'debit': 0,
                    'name': 'Test', 'ref': 'l10n_es_account_invoice_sequence'}
             ),
            (0, 0, {'account_id': account.id, 'credit': 0, 'debit': 1000,
                    'name': 'Test', 'ref': 'l10n_es_account_invoice_sequence'}
             )]
        self.move1 = acc_move_obj.create({
            'date': move_date,
            'period_id': period1.id,
            'journal_id': journal.id,
            'name': '/',
            'ref': 'Renumber Move 1',
            'state': 'draft',
            'line_id': acc_lines})
        self.move1.post()
        self.move2 = acc_move_obj.create({
            'date': fields.Date.from_string(move_date) + relativedelta(days=2),
            'period_id': period2.id,
            'journal_id': journal.id,
            'name': '/',
            'ref': 'Renumber Move 2',
            'state': 'draft',
            'line_id': acc_lines})
        self.move2.post()
        self.move3 = acc_move_obj.create({
            'date': fields.Date.from_string(move_date) + relativedelta(days=4),
            'period_id': period1.id,
            'journal_id': journal.id,
            'name': '/',
            'ref': 'Renumber Move 3',
            'state': 'draft',
            'line_id': acc_lines})
        self.move3.post()
        self.wiz_vals = {'journal_ids': [(6, 0, [journal.id])],
                         'period_ids': [(6, 0, [period1.id, period2.id])],
                         'number_next': 33}

    def test_normal_renumber_process(self):
        config = self.config_obj.new()
        config.renumber_by_period = True
        config.set_parameters()
        res = config.default_get(config._fields.keys())
        self.assertTrue(res.get('renumber_by_period', False))
        wiz = self.renumber_wiz_obj.create(self.wiz_vals)
        wiz.renumber()
        self.assertEqual(self.move1.name, '33')
        self.assertEqual(self.move3.name, '34')
        self.assertEqual(self.move2.name, '35')

    def test_no_period_renumber_process(self):
        config = self.config_obj.new()
        config.renumber_by_period = False
        config.set_parameters()
        res = config.default_get(config._fields.keys())
        self.assertFalse(res.get('renumber_by_period', False))
        wiz = self.renumber_wiz_obj.create(self.wiz_vals)
        wiz.renumber()
        self.assertEqual(self.move1.name, '33')
        self.assertEqual(self.move2.name, '34')
        self.assertEqual(self.move3.name, '35')

    def test_no_data_on_wizard(self):
        config = self.config_obj.new()
        config.renumber_by_period = False
        config.set_parameters()
        wiz = self.renumber_wiz_obj.create({})
        with self.assertRaises(exceptions.Warning):
            wiz.renumber()
