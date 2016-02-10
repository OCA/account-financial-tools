# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of account_journal_entry_posted_async,
#     an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     account_journal_entry_posted_async is free software:
#     you can redistribute it and/or modify it under the terms of the GNU
#     Affero General Public License as published by the Free Software
#     Foundation,either version 3 of the License, or (at your option) any
#     later version.
#
#     account_journal_entry_posted_async is distributed
#     in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
#     even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#     PURPOSE.  See the GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with account_journal_entry_posted_async.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import mock
from openerp.osv import fields
import openerp.tests.common as common


class AccountJournalEntryPostedAsyncTest(common.TransactionCase):

    def setUp(self):
        super(AccountJournalEntryPostedAsyncTest, self).setUp()
        cr, uid = self.cr, self.uid
        journal_model = self.registry('account.journal')
        self.journal_id = self.ref('account.bank_journal')
        self.account_id = self.ref('account.cash')
        self.partner_id = self.ref('base.res_partner_12')
        self.period_id = self.ref('account.period_6')
        journal_model.write(
            cr, uid, self.journal_id, {'entry_posted_async': True})

    def __get_account_line_info(self, name, debit, credit):
        cr, uid = self.cr, self.uid
        acc_move_line_model = self.registry('account.move.line')
        partner = acc_move_line_model.onchange_partner_id(
            cr, uid, [], None, self.partner_id,
            self.account_id,
            journal=self.journal_id)
        account = acc_move_line_model.onchange_account_id(
            cr, uid, [], account_id=self.account_id,
            partner_id=self.partner_id)

        # create a first line for the credit
        line_info = {'amount_currency': 0.0,
                     'account_id': self.account_id,
                     'credit': credit,
                     'debit': debit,
                     'name': name,
                     'partner_id': self.partner_id,
                     'ref': '20150527',
                     'tax_amount': 0.0,
                     'journal_id': self.journal_id,
                     'period_id': self.period_id,
                     'date_maturity': partner['value']['date_maturity'],
                     'account_tax_id': account['value']['account_tax_id']}
        return line_info

    def test_journal_config(self):
        journal_model = self.registry('account.journal')
        cr, uid = self.cr, self.uid
        journal_id = self.ref('account.bank_journal')
        journal_model.write(
            cr, uid, journal_id, {'entry_posted': False,
                                  'entry_posted_async': True})

        journal = journal_model.browse(cr, uid, journal_id)
        self.assertTrue(journal.entry_posted)

    def test_account_validate_async_1(self):
        """ Here we test that the validation is delayed when an
        account.move.line validating the balance of the move is created
        """
        acc_move_model = self.registry('account.move')
        acc_move_line_model = self.registry('account.move.line')
        cr, uid = self.cr, self.uid
        with mock.patch('openerp.addons.account_journal_entry_posted_async.'
                        'models.account_move.validate_one_move.delay'
                        ) as delay:

            # create on move
            move_id = acc_move_model.create(
                cr, uid,
                {'date': fields.date.today(),
                 'period_id': self.period_id,
                 'journal_id': self.journal_id,
                 'name': 'test move',
                 'ref': '20150527',
                 'state': 'draft'})
            # create a first line for the credit
            line_info = self.__get_account_line_info('Line1', 0.0, 1.0)
            line_info['move_id'] = move_id
            acc_move_line_model.create(cr, uid, line_info)
            # at this stage the delay is not called since the move is not
            # well balanced
            self.assertEqual(0, delay.call_count)

            # create a second line for the debit
            line_info = self.__get_account_line_info('Line2', 1.0, 0.0)
            line_info['move_id'] = move_id
            acc_move_line_model.create(cr, uid, line_info)

            # the delay must be called since the move is well balanced
            self.assertEqual(1, delay.call_count)

    def test_account_validate_async_2(self):
        """ Here we test that the validation is delayed when a balanced
        account.move is created
        """
        acc_move_model = self.registry('account.move')
        cr, uid = self.cr, self.uid
        with mock.patch('openerp.addons.account_journal_entry_posted_async.'
                        'models.account_move.validate_one_move.delay'
                        ) as delay:
            line_info_1 = self.__get_account_line_info('Line1', 0.0, 1.0)
            line_info_2 = self.__get_account_line_info('Line1', 1.0, 0.0)

            # create on move
            acc_move_model.create(
                cr, uid,
                {'date': fields.date.today(),
                 'period_id': self.period_id,
                 'journal_id': self.journal_id,
                 'name': 'test move',
                 'ref': '20150527',
                 'line_id': [(0, 0, line_info_1),
                             (0, 0, line_info_2)
                             ],
                 'state': 'draft'})
            # create a first line for the credit
            self.assertEqual(1, delay.call_count)
