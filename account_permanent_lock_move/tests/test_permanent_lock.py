# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
from openerp import fields, tools
from openerp.modules import get_module_resource
from openerp.tests import common
from openerp.exceptions import UserError


class PermanentLock(common.TransactionCase):

    def setUp(self):
        super(PermanentLock, self).setUp()
        tools.convert_file(self.cr, 'account',
                           get_module_resource('account', 'test',
                                               'account_minimal_test.xml'),
                           {}, 'init', False, 'test')
        self.account_move_obj = self.env["account.move"]
        self.account_move_line_obj = \
            self.env["account.move.line"]
        self.company_id = self.ref('base.main_company')
        self.partner = self.browse_ref("base.res_partner_12")
        self.account_id = self.ref("account.a_recv")
        self.account_id2 = self.ref("account.a_expense")
        self.journal_id = self.ref("account.bank_journal")
        self.wizard_obj = self.env["permanent.lock.date.wizard"]

    def test_name_completion(self):
        """Test complete partner_id from statement line label
        Test the automatic completion of the partner_id based if the name of
        the partner appears in the statement line label
        """

        # Create a move
        self.move = self.account_move_obj.create({
            'date': fields.Date.today(),
            'journal_id': self.journal_id,
            'line_ids': [(0, 0, {
                'account_id': self.account_id,
                'credit': 1000.0,
                'name': 'Credit line',
            }), (0, 0, {
                'account_id': self.account_id2,
                'debit': 1000.0,
                'name': 'Debit line',
            })]
        })

        # Call lock wizard on entry
        raised_lock_error = False
        try:
            self.wizard = self.wizard_obj.create({
                'company_id': self.company_id,
                'lock_date': fields.Date.today()
            })
            self.wizard.confirm_date()
        except UserError as ue:
            if 'entries are still unposted' in ue.name:
                raised_lock_error = True

        self.assertTrue(raised_lock_error,
                        "Permanent lock done even with unposted entry.")

        # Post entry and lock
        self.move.post()

        moves = self.env['account.move'].search(
            [('company_id', '=', self.company_id),
             ('date', '<=', fields.Date.today()),
             ('state', '=', 'draft')])
        moves.post()

        self.wizard = self.wizard_obj.create({
            'company_id': self.company_id,
            'lock_date': fields.Date.today()
        })
        self.wizard.confirm_date()

        # Try to lock the day before
        raised_lock_error = False
        try:
            yesterday = fields.Date.to_string(
                fields.Date.from_string(
                    fields.Date.today()) +
                datetime.timedelta(days=-1))
            self.wizard = self.wizard_obj.create({
                'company_id': self.company_id,
                'lock_date': yesterday
            })
            self.wizard.confirm_date()
        except UserError as ue:
            if 'permanent lock date in the past' in ue.name:
                raised_lock_error = True

        self.assertTrue(raised_lock_error,
                        "Permanent lock set the day before.")

        # Test that the move cannot be created, written, or cancelled
        raised_create_error = False
        raised_write_error = False
        raised_cancel_error = False
        try:
            self.move2 = self.account_move_obj.create({
                'date': fields.Date.today(),
                'journal_id': self.journal_id,
                'line_ids': [(0, 0, {
                    'account_id': self.account_id,
                    'credit': 1000.0,
                    'name': 'Credit line',
                }), (0, 0, {
                    'account_id': self.account_id2,
                    'debit': 1000.0,
                    'name': 'Debit line',
                })]
            })
        except UserError as ue:
            if 'permanent lock date' in ue.name:
                raised_create_error = True

        self.assertTrue(raised_create_error,
                        "Journal Entry could be created after locking!")

        try:
            self.move.write({'name': 'TEST'})
        except UserError as ue:
            if 'permanent lock date' in ue.name:
                raised_write_error = True

        self.assertTrue(raised_write_error,
                        "Journal Entry could be modified after locking!")

        try:
            self.move.button_cancel()
        except UserError as ue:
            if 'permanent lock date' in ue.name:
                raised_cancel_error = True

        self.assertTrue(raised_cancel_error,
                        "Journal Entry could be cancelled after locking!")
