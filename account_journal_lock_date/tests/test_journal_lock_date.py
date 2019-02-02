# Copyright 2017 ACSONE SA/NV
# Copyright 2018 XOE Corp. SAS <https://xoe.solutions>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields, tools
from odoo.modules import get_module_resource
from odoo.tests import common
from odoo.exceptions import ValidationError

from ..exceptions import JournalLockDateError


class TestJournalLockDate(common.TransactionCase):

    def setUp(self):
        super(TestJournalLockDate, self).setUp()
        tools.convert_file(self.cr, 'account',
                           get_module_resource('account', 'test',
                                               'account_minimal_test.xml'),
                           {}, 'init', False, 'test')
        self.account_move_obj = self.env["account.move"]
        self.account_move_line_obj = self.env["account.move.line"]
        self.company_id = self.ref('base.main_company')
        self.partner = self.browse_ref("base.res_partner_12")
        self.account = self.browse_ref("account.a_recv")
        self.account2 = self.browse_ref("account.a_expense")
        self.journal = self.browse_ref("account.bank_journal")
        self.env.user.write({'groups_id': [(5, None)]})
        self.journal.update_posted = True
        self.journal.company_id.period_lock_date = False
        self.journal.journal_lock_date_period_offset = False
        self.tomorrow = fields.Date.today() + timedelta(days=+1)
        self.yesterday = fields.Date.today() + timedelta(days=-1)
        self.three_days_ago = fields.Date.today() + timedelta(days=-3)

    def test_journal_lock_date_tracing_with_draft(self):
        # create a move and leave it in draft
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
        # Cannot change the date if it would affect moves in draft
        # They could not be validated any more unless by an "Adviser"
        with self.assertRaises(ValidationError):
            self.journal.company_id.period_lock_date = self.three_days_ago
            self.journal.journal_lock_date_period_offset = 3

    def test_journal_lock_date(self):
        self.env.user.write({
            'groups_id': [(4, self.ref('account.group_account_invoice'))],
        })
        self.assertFalse(self.env.user.has_group(
            'account.group_account_manager'))

        # create a move and post it without restrictions
        goodmove = self.account_move_obj.create({
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

        goodmove.post()

        # Now, set the lock date
        self.journal.company_id.period_lock_date = self.three_days_ago
        self.journal.journal_lock_date_period_offset = 3
        self.assertTrue(self.journal.journal_lock_date == fields.Date.today())

        onlockdate = self.account_move_obj.create({
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

        beforelockdate = self.account_move_obj.create({
            'date': self.yesterday,
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

        # Test that the move cannot be popsted or cancelled
        with self.assertRaises(JournalLockDateError):
            onlockdate.post()
        with self.assertRaises(JournalLockDateError):
            beforelockdate.post()
        with self.assertRaises(JournalLockDateError):
            onlockdate.button_cancel()
        with self.assertRaises(JournalLockDateError):
            beforelockdate.button_cancel()

        # create a move after ther lock date and post it
        move3 = self.account_move_obj.create({
            'date': self.tomorrow,
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
        self.journal.company_id.period_lock_date = self.three_days_ago
        self.journal.journal_lock_date_period_offset = 3
        self.assertTrue(self.journal.journal_lock_date == fields.Date.today())

        # advisers can post or cancel moves before or on the lock date
        onlockdate = self.account_move_obj.create({
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

        beforelockdate = self.account_move_obj.create({
            'date': self.yesterday,
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

        onlockdate.post()
        beforelockdate.post()
        onlockdate.button_cancel()
        beforelockdate.button_cancel()
