# -*- encoding: utf-8 -*-
# #############################################################################
#
# Account partner required module for OpenERP
#    Copyright (C) 2014 Acsone (http://acsone.eu).
#    @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime

from openerp.tests import common
from openerp import fields


class test_account_reversal(common.TransactionCase):

    def setUp(self):
        super(test_account_reversal, self).setUp()
        self.move_obj = self.env['account.move']
        self.move_line_obj = self.env['account.move.line']

    def _create_move(self, with_partner, amount=100, period=None):
        date = datetime.now()
        company_id = self.env.ref('base.main_company').id
        period = period or self.env.ref('account.period_0')

        journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'COD',
            'type': 'sale',
            'sequence_id': self.env.ref('account.sequence_sale_journal').id,
            'company_id': company_id})

        move_vals = {
            'journal_id': journal.id,
            'period_id': period.id,
            'date': date,
            'company_id': company_id,
        }

        # Why this doesn't work I don't know:
        # acct = self.ref('account.a_sale'
        account1, account2 = self.env['account.account'].search(
            [('company_id', '=', company_id), ('type', '=', 'other')])[:2]

        move_id = self.move_obj.create(move_vals)
        self.move_line_obj.create({
            'move_id': move_id.id,
            'name': '/',
            'debit': 0,
            'credit': amount,
            'company_id': company_id,
            'account_id': account1.id})
        move_line_id = self.move_line_obj.create(
            {
                'move_id': move_id.id,
                'name': '/',
                'debit': amount,
                'credit': 0,
                'account_id': account2.id,
                'company_id': company_id,
                'partner_id': self.ref('base.res_partner_1')
                if with_partner else False
            }
        )
        return move_line_id.move_id

    def _close_period(self, period_id):
        self.env.cr.execute('update account_journal_period '
                            'set state=%s where period_id=%s',
                            ('done', period_id))
        self.env.cr.execute('update account_period '
                            'set state=%s where id=%s',
                            ('done', period_id))
        self.env.invalidate_all()

    def test_reverse(self):
        move = self._create_move(with_partner=False)
        company_id = self.env.ref('base.main_company').id
        account1 = self.env['account.account'].search(
            [('company_id', '=', company_id), ('type', '=', 'other')])[0]
        movestr = ''.join(['%.2f%.2f%s' % (x.debit, x.credit,
                                           x.account_id == account1 and
                                           'aaaa' or 'bbbb')
                           for x in move.line_id])
        self.assertEqual(movestr, '100.000.00bbbb0.00100.00aaaa')
        yesterday_date = datetime(
            year=time.localtime().tm_year, month=3, day=3
        )
        yesterday = fields.Date.to_string(yesterday_date)
        reversed_move_ids = move.create_reversals(yesterday)
        reversed_moves = self.env['account.move'].browse(reversed_move_ids)
        movestr_reversed = ''.join(
            ['%.2f%.2f%s' % (x.debit, x.credit,
                             x.account_id == account1 and 'aaaa' or 'bbbb')
             for x in reversed_moves.line_id])
        self.assertEqual(movestr_reversed, '0.00100.00bbbb100.000.00aaaa')

    def test_reverse_closed_period(self):
        move_period = self.env.ref('account.period_0')
        move = self._create_move(with_partner=False, period=move_period)
        self._close_period(move_period.id)
        reversal_period = self.env.ref('account.period_1')
        move.create_reversals(reversal_date=reversal_period.date_start,
                              reversal_period_id=reversal_period.id)
