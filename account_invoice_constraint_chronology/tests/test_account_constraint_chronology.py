# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


def get_journal_check(self, value):
    sale_journal_obj = self.AccountJournal.env['account.journal'].\
        search([('type', '=', 'sale')], limit=1)
    journal = sale_journal_obj.copy()
    journal.check_chronology = value
    return journal


def create_simple_invoice(self, journal_id, date):
    invoice_account = self.env['account.account'].\
        search([('user_type_id', '=',
                 self.env.ref(
                     'account.data_account_type_receivable'
                 ).id)], limit=1).id
    invoice_line_account = self.env['account.account'].\
        search([('user_type_id', '=',
                 self.env.ref(
                     'account.data_account_type_expenses'
                 ).id)], limit=1).id
    analytic_account = self.env['account.analytic.account'].\
        create({'name': 'test account'})

    invoice = self.env['account.invoice'].create(
        {'partner_id': self.env.ref('base.res_partner_2').id,
         'account_id': invoice_account,
         'type': 'in_invoice',
         'journal_id': journal_id,
         'date_invoice': date,
         'state': 'draft',
         })
    # invoice.write({'internal_number': invoice.number})
    self.env['account.invoice.line'].create(
        {'product_id': self.env.ref('product.product_product_4').id,
         'quantity': 1.0,
         'price_unit': 100.0,
         'invoice_id': invoice.id,
         'name': 'product that cost 100',
         'account_id': invoice_line_account,
         'account_analytic_id': analytic_account.id,
         })
    return invoice


class TestAccountConstraintChronology(common.TransactionCase):

    def setUp(self):
        super(TestAccountConstraintChronology, self).setUp()
        self.AccountJournal = self.env['account.journal']
        self.Account = self.env['account.account']

    def test_invoice_draft(self):
        journal = get_journal_check(self, True)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date = yesterday.strftime(DEFAULT_SERVER_DATE_FORMAT)
        create_simple_invoice(self, journal.id, date)
        date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_2 = create_simple_invoice(self, journal.id, date)
        self.assertTrue((invoice_2.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_2.action_invoice_open()

    def test_invoice_validate(self):
        journal = get_journal_check(self, True)
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        date_tomorrow = tomorrow.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_1 = create_simple_invoice(self, journal.id, date_tomorrow)
        self.assertTrue((invoice_1.state == 'draft'),
                        "Initial invoice state is not Draft")
        invoice_1.action_invoice_open()
        date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_2 = create_simple_invoice(self, journal.id, date)
        self.assertTrue((invoice_2.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_2.action_invoice_open()

    def test_invoice_without_date(self):
        journal = get_journal_check(self, True)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date = yesterday.strftime(DEFAULT_SERVER_DATE_FORMAT)
        create_simple_invoice(self, journal.id, date)
        invoice_2 = create_simple_invoice(self, journal.id, False)
        self.assertTrue((invoice_2.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_2.action_invoice_open()
