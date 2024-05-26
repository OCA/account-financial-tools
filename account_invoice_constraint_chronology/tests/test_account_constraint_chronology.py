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
from openerp import workflow
from openerp.osv import orm
from datetime import datetime, timedelta

DB = common.DB
ADMIN_USER_ID = common.ADMIN_USER_ID


def get_simple_product_id(self):
    return self.registry('product.product').create(self.cr,
                                                   self.uid,
                                                   {'name': 'product_test_01',
                                                    'lst_price': 2000.00,
                                                    }, context={})


def get_journal_check(self, value):
    sale_journal_id = self.ref('account.sales_journal')
    journal_id = self.registry('account.journal').copy(self.cr,
                                                       self.uid,
                                                       sale_journal_id,
                                                       {},
                                                       context={})
    self.registry('account.journal').write(self.cr,
                                           self.uid,
                                           [journal_id],
                                           {'check_chronology': value},
                                           context={})
    return journal_id


def get_simple_account_invoice_line_values(self, product_id):
    return {'name': 'test',
            'account_id': self.ref('account.a_sale'),
            'price_unit': 2000.00,
            'quantity': 1,
            'product_id': product_id,
            }


def create_simple_invoice(self, journal_id, date):
    partner_id = self.ref('base.res_partner_2')
    product_id = get_simple_product_id(self)
    return self.env['account.invoice']\
        .create({'partner_id': partner_id,
                 'account_id':
                 self.ref('account.a_recv'),
                 'journal_id':
                 journal_id,
                 'date_invoice': date,
                 'invoice_line': [(0, 0, {'name': 'test',
                                          'account_id':
                                          self.ref('account.a_sale'),
                                          'price_unit': 2000.00,
                                          'quantity': 1,
                                          'product_id': product_id,
                                          }
                                   )
                                  ],
                 })


class TestAccountConstraintChronology(common.TransactionCase):

    def setUp(self):
        super(TestAccountConstraintChronology, self).setUp()

    def test_invoice_draft(self):
        journal_id = get_journal_check(self, True)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date = yesterday.strftime('%Y-%m-%d')
        create_simple_invoice(self, journal_id, date)
        date = today.strftime('%Y-%m-%d')
        invoice_2 = create_simple_invoice(self, journal_id, date)
        self.assertRaises(orm.except_orm, workflow.trg_validate, self.uid,
                          'account.invoice', invoice_2.id, 'invoice_open',
                          self.cr)

    def test_invoice_validate(self):
        journal_id = get_journal_check(self, True)
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        date = tomorrow.strftime('%Y-%m-%d')
        invoice = create_simple_invoice(self, journal_id, date)
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        date = today.strftime('%Y-%m-%d')
        invoice_2 = create_simple_invoice(self, journal_id, date)
        self.assertRaises(orm.except_orm, workflow.trg_validate, self.uid,
                          'account.invoice', invoice_2.id, 'invoice_open',
                          self.cr)

    def test_invoice_without_date(self):
        journal_id = get_journal_check(self, True)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date = yesterday.strftime('%Y-%m-%d')
        create_simple_invoice(self, journal_id, date)
        invoice_2 = create_simple_invoice(self, journal_id, False)
        self.assertRaises(orm.except_orm, workflow.trg_validate, self.uid,
                          'account.invoice', invoice_2.id, 'invoice_open',
                          self.cr)
