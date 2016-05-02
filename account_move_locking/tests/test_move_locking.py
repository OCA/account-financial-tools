# -*- coding: utf-8 -*-
# © 2015-2016 Camptocamp SA (Vincent Renaville)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
from openerp.tests import common
from openerp import fields, tools
from openerp.modules import get_module_resource
from openerp.exceptions import UserError


class TestMoveLocking(common.TransactionCase):

    def setUp(self):
        super(TestMoveLocking, self).setUp()
        self.company_a = self.browse_ref('base.main_company')
        tools.convert_file(self.cr, 'account',
                           get_module_resource('account', 'test',
                                               'account_minimal_test.xml'),
                           {}, 'init', False, 'test')
        self.account_move_obj = self.env["account.move"]
        self.account_move_line_obj = self.env["account.move.line"]
        self.wizard_obj = self.env["lock.account.move"]
        self.account_id = self.ref("account.a_recv")
        self.account_id2 = self.ref("account.a_expense")
        self.journal_id = self.ref("account.bank_journal")
        self.partner = self.browse_ref("base.res_partner_12")

    def test_move_lock(self):

        # Create entry for today
        self.move = self.account_move_obj.create({
            "date": fields.Date.today(),
            "journal_id": self.journal_id
        })

        self.account_move_line_obj.with_context(
            check_move_validity=False
        ).create({
            'account_id': self.account_id,
            'credit': 1000.0,
            'name': 'Credit line',
            'move_id': self.move.id,
        })

        self.account_move_line_obj.create({
            'account_id': self.account_id2,
            'debit': 1000.0,
            'name': 'Debit line',
            'move_id': self.move.id,
        })

        # Post the entry
        self.move.post()

        # Call lock wizard on entry
        self.wizard = self.wizard_obj.create({
            'journal_ids': [(6, 0, [self.journal_id])],
            'date_start': fields.Datetime.to_string(
                fields.Datetime.from_string(
                    fields.Datetime.now())
                + datetime.timedelta(days=-1)
            ),
            'date_end': fields.Datetime.to_string(
                fields.Datetime.from_string(
                    fields.Datetime.now())
                + datetime.timedelta(days=1)
            ),
        })
        self.wizard.lock_move()

        # Test that the move cannot be written or deleted
        raised_write_error = False
        raised_unlink_error = False
        try:
            self.move.write({'name': 'TEST'})
        except UserError as ue:
            if 'Move Locked!' in ue.name:
                raised_write_error = True

        self.assertTrue(raised_write_error,
                        "Journal Entry could be modified after locking!")

        try:
            self.move.unlink()
        except UserError as ue:
            if 'Move Locked!' in ue.name:
                raised_unlink_error = True

        self.assertTrue(raised_unlink_error,
                        "Journal Entry could be modified after locking!")
