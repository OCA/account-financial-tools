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
from openerp import exceptions
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openupgradelib.openupgrade import UserError


class TestAccountConstraintChronology(common.TransactionCase):

    def setUp(self):
        super(TestAccountConstraintChronology, self).setUp()

        # Needed to create invoice

        self.account_type1 = self.env['account.account.type'].\
            create({'name': 'acc type test 1',
                    'type': 'receivable',
                    'include_initial_balance': True})
        self.account_type2 = self.env['account.account.type']. \
            create({'name': 'acc type test 2',
                    'type': 'other',
                    'include_initial_balance': True})
        self.account_account = self.env['account.account'].\
            create({'name': 'acc test',
                    'code': 'X2020',
                    'user_type_id': self.account_type1.id,
                    'reconcile': True})
        self.account_account_line = self.env['account.account']. \
            create({'name': 'acc inv line test',
                    'code': 'X2021',
                    'user_type_id': self.account_type2.id,
                    'reconcile': True})
        self.sequence = self.env['ir.sequence'].create(
            {'name': 'Journal Sale',
             'prefix': 'SALE', 'padding': 6,
             'company_id': self.env.ref("base.main_company").id})
        self.account_journal_sale = self.env['account.journal']\
            .create({'name': 'Sale journal',
                     'code': 'SALE',
                     'type': 'sale',
                     'sequence_id': self.sequence.id})
        self.product = self.env['product.product'].create(
            {'name': 'product name'})
        self.analytic_account = self.env['account.analytic.account'].\
            create({'name': 'test account'})

    def get_journal_check(self, value):
        journal = self.account_journal_sale.copy()
        journal.check_chronology = value
        return journal

    def create_simple_invoice(self, journal_id, date):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': self.account_account.id,
            'type': 'in_invoice',
            'journal_id': journal_id,
            'date_invoice': date,
            'state': 'draft',
        })

        self.env['account.invoice.line'].create({
            'product_id': self.product.id,
            'quantity': 1.0,
            'price_unit': 100.0,
            'invoice_id': invoice.id,
            'name': 'product that cost 100',
            'account_id': self.account_account_line.id,
            'account_analytic_id': self.analytic_account.id,
        })
        return invoice

    def test_invoice_draft(self):
        journal = self.get_journal_check(True)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date = yesterday.strftime(DEFAULT_SERVER_DATE_FORMAT)
        self.create_simple_invoice(journal.id, date)
        date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_2 = self.create_simple_invoice(journal.id, date)
        self.assertTrue((invoice_2.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_2.action_invoice_open()

    def test_invoice_validate(self):
        journal = self.get_journal_check(True)
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        date_tomorrow = tomorrow.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_1 = self.create_simple_invoice(journal.id, date_tomorrow)
        self.assertTrue((invoice_1.state == 'draft'),
                        "Initial invoice state is not Draft")
        invoice_1.action_invoice_open()
        date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_2 = self.create_simple_invoice(journal.id, date)
        self.assertTrue((invoice_2.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_2.action_invoice_open()

    def test_invoice_without_date(self):
        journal = self.get_journal_check(True)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date = yesterday.strftime(DEFAULT_SERVER_DATE_FORMAT)
        self.create_simple_invoice(journal.id, date)
        invoice_2 = self.create_simple_invoice(journal.id, False)
        self.assertTrue((invoice_2.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_2.action_invoice_open()
