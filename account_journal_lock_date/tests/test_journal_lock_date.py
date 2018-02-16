# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo import fields, tools
from odoo.modules import get_module_resource
from odoo.tests import common

from ..exceptions import JournalLockDateError
from ..exceptions import JournalPermanentLockDateError
from ..exceptions import AccesRightsLockError


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
        self.cust_invoices_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'), ('code', '=', 'INV')
        ])
        self.entries = self.env['account.move'].search([
            ('journal_id', '=', self.cust_invoices_journal.id)
        ])
        self.journals = self.env['account.journal'].search([])

    def test_journal_lock_date(self):
        self.browse_ref('account.group_account_manager').sudo().write({
            'users': [(3, self.env.user.id)],
        })
        self.assertFalse(
            self.env.user.has_group('account.group_account_manager'))
        # create a move and post it
        move = self.account_move_obj.create({
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
        move.post()
        # lock journal
        vals = {
            'journal_ids': [(6, 0, [self.journal.id])],
            'lock_date': fields.Date.today(),
        }
        lock_wiz = self.env['wizard.lock.account.journal'].create(vals)
        lock_wiz.execute()

        self.assertTrue(move.locked)
        # Test that the move cannot be created, written, or cancelled
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

        with self.assertRaises(JournalLockDateError):
            move.write({'name': 'TEST'})

        with self.assertRaises(JournalLockDateError):
            move.button_cancel()

        with self.assertRaises(JournalLockDateError):
            move.unlink()

        # create a move after ther lock date and post it
        tomorrow = date.today() + timedelta(days=1)
        move3 = self.account_move_obj.create({
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
        move3.post()
        # Check update moves locked with date upper than lock date.
        with self.assertRaises(AccesRightsLockError):
            self.account_move_obj.create({
                'date': tomorrow,
                'journal_id': self.journal.id,
                'locked': True,
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

    def test_journal_lock_date_adviser(self):
        """ The journal lock date for Advisers """
        self.env.user.sudo().write({
            'groups_id': [(4, self.ref('account.group_account_manager'))],
        })
        self.assertTrue(
            self.env.user.has_group('account.group_account_manager'))

        moves = self.account_move_obj.search([])
        moves.post()

        # lock journal
        vals = {
            'journal_ids': [(4, self.journal.id)],
            'lock_date': fields.Date.today(),
        }
        lock_wiz = self.env['wizard.lock.account.journal'].create(vals)
        lock_wiz.execute()

        # advisers can create moves before or on the lock date
        move = self.account_move_obj.create({
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
        move.post()

        # lock journal permananet
        vals = {
            'journal_ids': [(4, self.journal.id)],
            'lock_date': fields.Date.today(),
            'permanent_lock': True,
        }
        lock_wiz = self.env['wizard.lock.account.journal'].create(vals)
        lock_wiz.execute()

        # neither advisers cannot create moves before or on the lock date
        with self.assertRaises(JournalPermanentLockDateError):
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

    def test_locking(self):
        moves = self.account_move_obj.search([])
        moves.post()
        vals = {
            'journal_ids': [(4, self.cust_invoices_journal.id)],
            'lock_date': fields.Date.today(),
        }
        lock_wiz = self.env['wizard.lock.account.journal'].create(vals)
        lock_wiz.execute()
        for move in self.entries:
            self.assertTrue(move.locked)

    def test_wizard_lock_dates(self):
        vals = {
            'journal_ids': [(6, 0, self.journals._ids)],
            'lock_date': fields.Date.today(),
        }
        with self.assertRaises(JournalLockDateError):
            lock_wiz = self.env['wizard.lock.account.journal'].create(vals)
            lock_wiz.execute()

        moves = self.account_move_obj.search([('state', '=', 'draft')])
        moves.post()
        self.env.user.sudo().write({
            'groups_id': [(4, self.ref('account.group_account_manager'))],
        })
        self.assertTrue(
            self.env.user.has_group('account.group_account_manager'))

        # create a move and post it
        yesterday = date.today() + timedelta(days=-1)
        tomorrow = date.today() + timedelta(days=1)
        move = self.account_move_obj.create({
            'date': yesterday,
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
        move1 = self.account_move_obj.create({
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
        move1.post()
        move2 = self.account_move_obj.create({
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
        move2.post()

        # lock journal
        move.company_id.sudo().write({
            'fiscalyear_lock_date': fields.Date.today(),
        })
        vals.update({'lock_date': yesterday})
        with self.assertRaises(JournalLockDateError):
            lock_wiz = self.env['wizard.lock.account.journal'].create(vals)
            lock_wiz.execute()

        move.company_id.sudo().write({
            'fiscalyear_lock_date': False,
        })

        vals.update({'lock_date': tomorrow})
        lock_wiz1 = self.env['wizard.lock.account.journal'].create(vals)
        lock_wiz1.execute()
        self.assertTrue(move.locked)
        self.assertTrue(move1.locked)
        self.assertTrue(move2.locked)

        vals.update({'lock_date': fields.Date.today()})
        lock_wiz2 = self.env['wizard.lock.account.journal'].create(vals)
        lock_wiz2.execute()
        self.assertTrue(move.locked)
        self.assertTrue(move1.locked)
        self.assertFalse(move2.locked)
