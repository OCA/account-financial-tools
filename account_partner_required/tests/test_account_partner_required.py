# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account partner required module for OpenERP
#    Copyright (C) 2014 Acsone (http://acsone.eu). All Rights Reserved
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

from datetime import datetime

from openerp.tests import common
from openerp.osv import orm


class test_account_partner_required(common.TransactionCase):

    def setUp(self):
        super(test_account_partner_required, self).setUp()
        self.account_obj = self.registry('account.account')
        self.account_type_obj = self.registry('account.account.type')
        self.move_obj = self.registry('account.move')
        self.move_line_obj = self.registry('account.move.line')

    def _create_move(self, with_partner, amount=100):
        date = datetime.now()
        period_id = self.registry('account.period').find(self.cr, self.uid, date, context={'account_period_prefer_normal': True})[0]
        move_vals = {
            'journal_id': self.ref('account.sales_journal'),
            'period_id': period_id,
            'date': date,
        }
        move_id = self.move_obj.create(self.cr, self.uid, move_vals)
        self.move_line_obj.create(self.cr, self.uid,
                 {'move_id': move_id,
                  'name': '/',
                  'debit': 0,
                  'credit': amount,
                  'account_id': self.ref('account.a_sale'),
                 })
        move_line_id = self.move_line_obj.create(self.cr, self.uid,
                {'move_id': move_id,
                 'name': '/',
                 'debit': amount,
                 'credit': 0,
                 'account_id': self.ref('account.a_recv'),
                 'partner_id': self.ref('base.res_partner_1') if with_partner else False,
                })
        return move_line_id

    def _set_partner_policy(self, policy, aref='account.a_recv'):
        account_type = self.account_obj.browse(self.cr, self.uid,
                                          self.ref(aref)).user_type
        self.account_type_obj.write(self.cr, self.uid, account_type.id,
                               {'partner_policy': policy})

    def test_optional(self):
        self._create_move(with_partner=False)
        self._create_move(with_partner=True)

    def test_always_no_partner(self):
        self._set_partner_policy('always')
        with self.assertRaises(orm.except_orm):
            self._create_move(with_partner=False)

    def test_always_no_partner_0(self):
        # accept missing partner when debit=credit=0
        self._set_partner_policy('always')
        self._create_move(with_partner=False, amount=0)

    def test_always_with_partner(self):
        self._set_partner_policy('always')
        self._create_move(with_partner=True)

    def test_never_no_partner(self):
        self._set_partner_policy('never')
        self._create_move(with_partner=False)

    def test_never_with_partner(self):
        self._set_partner_policy('never')
        with self.assertRaises(orm.except_orm):
            self._create_move(with_partner=True)

    def test_never_with_partner_0(self):
        # accept partner when debit=credit=0
        self._set_partner_policy('never')
        self._create_move(with_partner=True, amount=0)

    def test_always_remove_partner(self):
        # remove partner when policy is always
        self._set_partner_policy('always')
        line_id = self._create_move(with_partner=True)
        with self.assertRaises(orm.except_orm):
            self.move_line_obj.write(self.cr, self.uid, line_id,
                                     {'partner_id': False})

    def test_change_account(self):
        self._set_partner_policy('always', aref='account.a_pay')
        line_id = self._create_move(with_partner=False)
        # change account to a_pay with policy always but missing partner
        with self.assertRaises(orm.except_orm):
            self.move_line_obj.write(self.cr, self.uid, line_id,
                                     {'account_id': self.ref('account.a_pay')})
        # change account to a_pay with policy always with partner -> ok
        self.move_line_obj.write(self.cr, self.uid, line_id,
                                 {'account_id': self.ref('account.a_pay'),
                                  'partner_id': self.ref('base.res_partner_1')})
