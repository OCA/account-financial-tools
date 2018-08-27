# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from openerp import fields, tools
from openerp.modules import get_module_resource
from openerp.tests import common

from ..models.account_move import JournalLockDateError


class TestJournalLockDate(common.TransactionCase):

    def setUp(self):
        super(TestJournalLockDate, self).setUp()
        tools.convert_file(self.cr, 'account',
                           get_module_resource('account', 'test',
                                               'account_minimal_test.xml'),
                           {}, 'init', False, 'test')
        self.account_move_obj = self.env["account.move"]
        self.account_move_line_obj = \
            self.env["account.move.line"]

        self.company_id = self.ref('base.main_company')
        self.partner = self.browse_ref("base.res_partner_2")
        self.account = self.browse_ref("account.a_recv")
        self.account2 = self.browse_ref("account.a_expense")
        self.journal = self.browse_ref("account.bank_journal")

    def set_group_account_manager(self):
        self.env.user.write({
            'groups_id': [(4, self.ref('account.group_account_manager'))],
        })
        self.assertTrue(self.env.user.has_group(
            'account.group_account_manager'))

    def unset_group_account_manager(self):
        self.env.user.write({
            'groups_id': [(3, self.ref('account.group_account_manager'))],
        })
        self.assertFalse(self.env.user.has_group(
            'account.group_account_manager'))

    def create_move(self):
        """create a move and post it"""
        move = self.account_move_obj.create({
            'date': fields.Date.today(),
            'journal_id': self.journal.id,
            'line_ids': [
                (0, 0, {
                    'account_id': self.account.id,
                    'credit': 1000.0,
                    'name': 'Credit line'}),
                (0, 0, {
                    'account_id': self.account2.id,
                    'debit': 1000.0,
                    'name': 'Debit line',
            })]
        })
        move.post()
        return move

    def test_create_account_move(self):
        self.unset_group_account_manager()
        self.create_move()

    def test_create_account_move_on_locked_journal(self):
        """Test that the move cannot be created."""
        self.unset_group_account_manager()
        self.journal.journal_lock_date = fields.Date.today()

        with self.assertRaises(JournalLockDateError):
            self.account_move_obj.create({
                'date': fields.Date.today(),
                'journal_id': self.journal.id,
                'line_ids': [(0, 0, {
                    'account_id': self.account.id,
                    'credit': 1000.0,
                    'name': 'Credit line',
                }), (0, 0, {
                    'account_id': self.account2.id,
                    'debit': 1000.0,
                    'name': 'Debit line',
                })]
            })

    def test_update_account_move_on_locked_journal(self):
        """Test that the move cannot be written"""
        self.unset_group_account_manager()
        move = self.create_move()
        self.journal.journal_lock_date = fields.Date.today()

        with self.assertRaises(JournalLockDateError):
            move.write({'name': 'TEST'})

    def test_cancel_account_move_on_locked_journal(self):
        """Test that the move cannot be cancelled"""
        self.unset_group_account_manager()
        move = self.create_move()
        self.journal.journal_lock_date = fields.Date.today()
        with self.assertRaises(JournalLockDateError):
            move.button_cancel()

    def test_update_account_move_on_unlocked_journal(self):
        """Create a move after their lock date and post it"""
        self.unset_group_account_manager()
        self.journal.journal_lock_date = fields.Date.today()
        tomorrow = date.today() + timedelta(days=1)
        move = self.account_move_obj.create({
            'date': tomorrow,
            'journal_id': self.journal.id,
            'line_ids': [(0, 0, {
                'account_id': self.account.id,
                'credit': 1000.0,
                'name': 'Credit line',
            }), (0, 0, {
                'account_id': self.account2.id,
                'debit': 1000.0,
                'name': 'Debit line',
            })]
        })
        move.post()

    def test_journal_lock_date_adviser(self):
        """The journal lock date is ignored for Advisers """
        self.set_group_account_manager()
        self.journal.journal_lock_date = fields.Date.today()

        # advisers can create moves before or on the lock date
        self.account_move_obj.create({
            'date': fields.Date.today(),
            'journal_id': self.journal.id,
            'line_ids': [(0, 0, {
                'account_id': self.account.id,
                'credit': 1000.0,
                'name': 'Credit line',
            }), (0, 0, {
                'account_id': self.account2.id,
                'debit': 1000.0,
                'name': 'Debit line',
            })]
        })

