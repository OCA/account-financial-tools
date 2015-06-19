# -*- coding: utf-8 -*-
#
#
#    Authors: Adrien Peiffer
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
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
#

import openerp.tests.common as common
from openerp.exceptions import except_orm
from datetime import datetime
from psycopg2 import IntegrityError


def get_simple_account_move_values(self, period_id, journal_id):
    sale_product_account_id = self.ref('account.a_sale')
    cash_account_id = self.ref('account.cash')
    partner_id = self.ref('base.res_partner_2')
    year = datetime.now().strftime('%Y')
    return {'partner_id': partner_id,
            'period_id': period_id,
            'date': year + '-01-01',
            'journal_id': journal_id,
            'line_id': [(0, 0, {'name': 'test',
                                'account_id': cash_account_id,
                                'debit': 50.0,
                                }),
                        (0, 0, {'name': 'test_conterpart',
                                'account_id': sale_product_account_id,
                                'credit': 50.0,
                                })
                        ]
            }


def close_period(self, period_id, context=None):
    close_period_wizard_id =\
        self.registry('account.period.close').create(self.cr,
                                                     self.uid,
                                                     {'sure': True
                                                      },
                                                     context=context)
    context.update({'active_ids': [period_id]})
    self.registry('account.period.close')\
        .data_save(self.cr,
                   self.uid,
                   [close_period_wizard_id],
                   context=context)


def create_journal_period(self, period_id, journal_id, context):
    jour_per_obj = self.registry('account.journal.period')
    journal_period_id = jour_per_obj.create(self.cr,
                                            self.uid,
                                            {'period_id': period_id,
                                             'journal_id': journal_id,
                                             },
                                            context=context)
    return journal_period_id


def journal_period_done(self, journal_period_id, context):
    jour_per_obj = self.registry('account.journal.period')
    jour_per_obj.action_done(self.cr,
                             self.uid,
                             [journal_period_id],
                             context=context)


def journal_period_draft(self, journal_period_id, context):
    jour_per_obj = self.registry('account.journal.period')
    jour_per_obj.action_draft(self.cr,
                              self.uid,
                              [journal_period_id],
                              context=context)


def get_journal_copy_id(self, journal_id, context=None):
    return self.registry('account.journal').copy(self.cr, self.uid,
                                                 journal_id, {}, context)


def create_fiscalyear(self, year, company_id):
    fiscalyear_obj = self.registry('account.fiscalyear')
    fiscalyear_id = fiscalyear_obj.create(self.cr, self.uid, {
        'name': year,
        'code': year,
        'date_start': year + '-01-01',
        'date_stop': year + '-12-31',
        'company_id': company_id
    })
    fiscalyear_obj.create_period(self.cr, self.uid, [fiscalyear_id])
    return fiscalyear_id


class TestAccountJournalPeriodClose(common.TransactionCase):

    def setUp(self):
        super(TestAccountJournalPeriodClose, self).setUp()
        company_id = self.ref('base.main_company')
        fiscalyear_id = create_fiscalyear(self, '2013', company_id)
        journal_id = self.ref('account.sales_journal')
        self.period_id = self.registry('account.period')\
            .search(self.cr, self.uid, [('fiscalyear_id', '=', fiscalyear_id)],
                    limit=1)[0]
        self.journal_id = get_journal_copy_id(self, journal_id)

    def test_close_period_open_journal(self):
        context = {}
        close_period(self, self.period_id, context)
        journal_period_id = create_journal_period(self,
                                                  self.period_id,
                                                  self.journal_id,
                                                  context)
        journal_period_draft(self, journal_period_id, context)
        self.registry('account.move')\
            .create(self.cr,
                    self.uid,
                    get_simple_account_move_values(self,
                                                   self.period_id,
                                                   self.journal_id),
                    context=context)
        # Here, no exception should be raised because the journal's state is
        # draft although the period is closed

    def test_open_period_close_journal(self):
        context = {}
        journal_period_id = create_journal_period(self,
                                                  self.period_id,
                                                  self.journal_id,
                                                  context)
        journal_period_done(self, journal_period_id, context)
        move_values = get_simple_account_move_values(self,
                                                     self.period_id,
                                                     self.journal_id)
        # I check if the exception is correctly raised at create of an account
        # move which is linked with a closed journal
        self.assertRaises(except_orm,
                          self.registry('account.move').create,
                          self.cr, self.uid, move_values, context=context)

    def test_change_journal_on_move(self):
        context = {}
        journal_cash_id = self.ref('account.cash_journal')
        journal_period_id = create_journal_period(self,
                                                  self.period_id,
                                                  self.journal_id,
                                                  context)
        journal_period_done(self, journal_period_id, context)
        move_values = get_simple_account_move_values(self,
                                                     self.period_id,
                                                     journal_cash_id)
        self.registry('account.move').create(self.cr,
                                             self.uid,
                                             move_values,
                                             context=context)
        # Standard of Odoo doesn't check account_journal_period at write on
        # account_move
        # issue on Odoo github : #1633

        # I check if the exception is correctly raised
        # self.assertRaises(except_orm,
        #                   self.registry('account.move').write,
        #                   self.cr, self.uid, [move_id],
        #                   {'journal_id': journal_id}, context=context)

    def test_draft_move_close_journal(self):
        context = {}

        jour_per_obj = self.registry('account.journal.period')
        move_values = get_simple_account_move_values(self,
                                                     self.period_id,
                                                     self.journal_id)
        self.registry('account.move').create(self.cr,
                                             self.uid,
                                             move_values,
                                             context=context)
        journal_period_ids =\
            jour_per_obj.search(self.cr,
                                self.uid,
                                [('period_id', '=', self.period_id),
                                 ('journal_id', '=', self.journal_id),
                                 ],
                                context=context)
        # I check if the exception is correctly raised at closing journal that
        # contains some draft account move
        self.assertRaises(except_orm,
                          jour_per_obj.action_done,
                          self.cr, self.uid, journal_period_ids,
                          context=context)

    def test_duplicate_journal_period(self):
        context = {}
        create_journal_period(self, self.period_id, self.journal_id, context)
        # I check if the exception is correctly raised at adding both same
        # journal on a period
        self.cr._default_log_exceptions = False
        try:
            self.assertRaises(IntegrityError,
                              create_journal_period,
                              self, self.period_id, self.journal_id, context)
        finally:
            self.cr._default_log_exceptions = True
