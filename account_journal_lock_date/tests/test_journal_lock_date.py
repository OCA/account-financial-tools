# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo import tools
from odoo.modules import get_module_resource
from odoo.tests import common

from ..exceptions import JournalLockDateError


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
        self.partner = self.browse_ref("base.res_partner_12")
        self.account = self.browse_ref("account.a_recv")
        self.account2 = self.browse_ref("account.a_expense")
        self.journal = self.browse_ref("account.bank_journal")

    def test_journal_lock_date(self):
        self.env.user.write({
            'groups_id': [(3, self.ref('base.group_system'))],
        })
        self.env.user.write({
            'groups_id': [(3, self.ref('account.group_account_manager'))],
        })
        self.assertFalse(self.env.user.has_group(
            'account.group_account_manager'))

        # create a move and post it
        move = self.account_move_obj.create({
            'date': date.today(),
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
        # lock journal, set 'Lock Date for Non-Advisers'
        self.journal.period_lock_date = (date.today() + timedelta(days=2))
        # Test that the move cannot be created, written, or cancelled
        with self.assertRaises(JournalLockDateError):
            self.account_move_obj.create({
                'date': date.today(),
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

        with self.assertRaises(JournalLockDateError):
            move.write({'name': 'TEST'})

        # allow cancel posted move
        self.journal.update_posted = True
        with self.assertRaises(JournalLockDateError):
            move.button_cancel()

        # create a move after the 'Lock Date for Non-Advisers' and post it
        move3 = self.account_move_obj.create({
            'date': self.journal.period_lock_date + timedelta(days=3),
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
        move3.post()

    def test_journal_lock_date_adviser(self):
        """ The journal lock date is ignored for Advisers """
        self.env.user.write({
            'groups_id': [(4, self.ref('account.group_account_manager'))],
        })
        self.assertTrue(self.env.user.has_group(
            'account.group_account_manager'))
        # create a move and post it
        move = self.account_move_obj.create({
            'date': date.today(),
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
        # lock journal. Set 'Lock Date'
        self.journal.fiscalyear_lock_date = date.today() + timedelta(days=2)
        # lock journal. Set 'Lock Date for Non-Advisers'
        self.journal.period_lock_date = date.today() + timedelta(days=4)
        # Advisers cannot create, write, or cancel moves before 'Lock Date'
        with self.assertRaises(JournalLockDateError):
            self.account_move_obj.create({
                'date': date.today(),
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
        with self.assertRaises(JournalLockDateError):
            move.write({'name': 'TEST'})
        # allow cancel posted move
        self.journal.update_posted = True
        with self.assertRaises(JournalLockDateError):
            move.button_cancel()
        # Advisers can create movements on a date after the 'Lock Date'
        # even if that date is before and inclusive of
        # the 'Lock Date for Non-Advisers' (self.journal.period_lock_date)
        move3 = self.account_move_obj.create({
            'date': self.journal.period_lock_date,
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
        move3.post()
