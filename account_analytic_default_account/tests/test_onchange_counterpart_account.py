# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Damien Crier
#    Copyright 2015 Camptocamp SA
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

from openerp.tests import common


class testOnChange(common.TransactionCase):

    def setUp(self):
        super(testOnChange, self).setUp()
        self.ana_acc_def_obj = self.registry('account.analytic.default')
        self.acc_voucher_obj = self.registry('account.voucher')
        # analytic defaults account creation
        agrolait = self.ref('account.analytic_agrolait')
        expense = self.ref('account.income_fx_expense')
        income = self.ref('account.income_fx_income')
        self.account_1 = (
            self.ana_acc_def_obj.create(self.cr,
                                        self.uid,
                                        {
                                            'analytic_id': agrolait,
                                            'account_id': expense
                                        }
                                        )
        )
        self.account_2 = (
            self.ana_acc_def_obj.create(self.cr,
                                        self.uid,
                                        {
                                            'analytic_id': agrolait,
                                            'account_id': income
                                        })
        )

    def test_retrieve_analytic_account(self):
        res1 = self.acc_voucher_obj.onchange_writeoff_acc_id(
            self.cr, self.uid, [], self.ref('account.income_fx_expense'))
        res2 = self.acc_voucher_obj.onchange_writeoff_acc_id(
            self.cr, self.uid, [], self.ref('account.income_fx_income'))

        self.assertEqual(self.ref('account.analytic_agrolait'), res1.get(
            'value', {}).get('analytic_id', False))
        self.assertEqual(self.ref('account.analytic_agrolait'), res2.get(
            'value', {}).get('analytic_id', False))
