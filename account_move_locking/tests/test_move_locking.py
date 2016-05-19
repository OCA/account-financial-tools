# -*- coding: utf-8 -*-
# © 2015-2016 Camptocamp SA (Vincent Renaville)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
from openerp.tests import common
from openerp import fields, tools
from openerp.modules import get_module_resource
from openerp.exceptions import UserError
from dateutil.relativedelta import relativedelta


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
        self.date_range_obj = self.env["date.range"]
        self.date_range_type_obj = self.env["date.range.type"]
        self.lock_wizard_obj = self.env["date.range.lock"]
        self.unlock_wizard_obj = self.env["date.range.unlock"]
        self.account_id = self.ref("account.a_recv")
        self.account_id2 = self.ref("account.a_expense")
        self.journal_id = self.ref("account.bank_journal")
        self.fiscal_year_type = self.ref("account_fiscal_year.fiscalyear")
        self.partner = self.browse_ref("base.res_partner_12")

    def test_move_lock(self):
        self.period_type = self.date_range_type_obj.create({
            'name': 'Period',
            'allow_overlap': False
        })

        month_first = fields.Date.to_string(
            fields.Date.from_string(
                fields.Date.today()
            ) + relativedelta(day=1)
        )
        month_last = fields.Date.to_string(
            fields.Date.from_string(
                fields.Date.today()
            ) + relativedelta(day=1, days=-1, months=1)
        )

        # Create period for this month
        self.period = self.date_range_obj.create({
            'name': 'Period',
            'type_id': self.period_type.id,
            'date_start': month_first,
            'date_end': month_last
        })
        self.assertTrue(self.period.lock_state == 'unlocked',
                        "Period is not unlocked!")

        # Create FY for this year
        self.fiscalyear = self.date_range_obj.create({
            'name': 'Fiscal Year',
            'type_id': self.fiscal_year_type,
            'date_start': fields.Date.today()[:4] + '-01-01',
            'date_end': fields.Date.today()[:4] + '-12-31'
        })
        self.assertTrue(self.fiscalyear.lock_state == 'unlocked',
                        "Fiscal Year is not unlocked!")

        # Create entry for today
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
        self.move.post()

        # TEST 1
        # Lock partially period
        self.wizard = self.lock_wizard_obj.create({
            'date_range_id': self.period.id,
            'journal_ids': [(6, 0, [self.journal_id])]
        })
        self.wizard.lock()
        self.assertTrue(self.period.lock_state == 'partial',
                        "Period was not partially locked!")

        # Now, unlock it and retry
        self.wizard2 = self.unlock_wizard_obj.create({
            'date_range_id': self.period.id
        })
        self.wizard2.unlock()
        self.assertTrue(self.period.lock_state == 'unlocked',
                        "Period was not unlocked!")

        # Now, lock the FY
        self.wizard3 = self.lock_wizard_obj.create({
            'date_range_id': self.fiscalyear.id
        })
        self.wizard3.lock()
        self.assertTrue(self.fiscalyear.lock_state == 'locked',
                        "Fiscal Year was not locked!")
        self.assertTrue(self.period.lock_state == 'locked',
                        "Period was not locked!")

        # Test that the move cannot be deleted, created, or written
        raised_create_error = False
        raised_write_error = False
        raised_unlink_error = False
        try:
            self.move.unlink()
        except UserError as ue:
            if 'Date Range Period is locked!' in ue.name:
                raised_unlink_error = True

        self.assertTrue(raised_unlink_error,
                        "Journal Entry could be deleted after locking!")

        try:
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
        except UserError as ue:
            if 'Date Range Period is locked!' in ue.name:
                raised_create_error = True

        self.assertTrue(raised_create_error,
                        "Journal Entry could be created after locking!")

        try:
            self.move.write({'name': 'TEST'})
        except UserError as ue:
            if 'Date Range Period is locked!' in ue.name:
                raised_write_error = True

        self.assertTrue(raised_write_error,
                        "Journal Entry could be modified after locking!")
