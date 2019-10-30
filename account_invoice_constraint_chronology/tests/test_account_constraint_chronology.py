# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

import odoo.tests.common as common
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


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
        self.sequence_purchase = self.env['ir.sequence'].create(
            {'name': 'Journal Purchase',
             'prefix': 'PURCHASE', 'padding': 6,
             'company_id': self.env.ref("base.main_company").id})
        self.account_journal_sale = self.env['account.journal']\
            .create({'name': 'Sale journal',
                     'code': 'SALE',
                     'type': 'sale',
                     'sequence_id': self.sequence.id})
        self.account_journal_purchase = self.env['account.journal']\
            .create({'name': 'Purchase journal',
                     'code': 'PURCHASE',
                     'type': 'purchase',
                     'sequence_id': self.sequence_purchase.id})
        self.product = self.env['product.product'].create(
            {'name': 'product name'})
        self.analytic_account = self.env['account.analytic.account'].\
            create({'name': 'test account'})

    def get_journal_check(self, value):
        journal = self.account_journal_sale.copy()
        journal.check_chronology = value
        return journal

    def get_journal_purchase_check(self, value):
        journal = self.account_journal_purchase.copy()
        journal.check_chronology = value
        return journal

    def create_simple_invoice(self, journal_id, date_invoice, date, type_invoice):
        vals = {
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': self.account_account.id,
            'type': type_invoice,
            'journal_id': journal_id,
            'date_invoice': date_invoice,
            'state': 'draft',
        }
        if date:
            vals.update(date=date)
        invoice = self.env['account.invoice'].create(vals)

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
        journal_purchase = self.get_journal_purchase_check(True)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date_yesterday = yesterday.strftime(DEFAULT_SERVER_DATE_FORMAT)
        date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        # test sale
        self.create_simple_invoice(
            journal.id, date_invoice=date_yesterday, date=date_yesterday,
            type_invoice='out_invoice')
        invoice_2 = self.create_simple_invoice(
            journal.id, date_invoice=date, date=date, type_invoice='out_invoice')
        self.assertTrue((invoice_2.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_2.action_invoice_open()
        # test purchase
        self.create_simple_invoice(
            journal_purchase.id, date_invoice=date_yesterday, date=False,
            type_invoice='in_invoice')
        invoice_3 = self.create_simple_invoice(
            journal_purchase.id, date_invoice=date, date=False,
            type_invoice='in_invoice')
        self.assertTrue((invoice_3.state == 'draft'),
                        "Initial invoice state is not Draft")
        invoice_3.action_invoice_open()
        self.assertTrue((invoice_3.state == 'open'), "Invoice state is not Open")

    def test_invoice_validate(self):
        journal = self.get_journal_check(True)
        journal_purchase = self.get_journal_purchase_check(True)
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        date_tomorrow = tomorrow.strftime(DEFAULT_SERVER_DATE_FORMAT)
        # test sale
        invoice_1 = self.create_simple_invoice(
            journal.id, date_invoice=date_tomorrow, date=date_tomorrow,
            type_invoice='out_invoice')
        self.assertTrue((invoice_1.state == 'draft'),
                        "Initial invoice state is not Draft")
        invoice_1.action_invoice_open()
        date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_2 = self.create_simple_invoice(
            journal.id, date_invoice=date, date=date, type_invoice='out_invoice')
        self.assertTrue((invoice_2.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_2.action_invoice_open()
        # test purchase
        invoice_3 = self.create_simple_invoice(
            journal_purchase.id, date_invoice=date_tomorrow, date=date_tomorrow,
            type_invoice='in_invoice')
        self.assertTrue((invoice_3.state == 'draft'),
                        "Initial invoice state is not Draft")
        invoice_3.action_invoice_open()
        date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_4 = self.create_simple_invoice(
            journal_purchase.id, date_invoice=date, date=date,
            type_invoice='in_invoice')
        self.assertTrue((invoice_4.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_4.action_invoice_open()

    def test_invoice_without_date(self):
        journal = self.get_journal_check(True)
        journal_purchase = self.get_journal_purchase_check(True)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date_yesterday = yesterday.strftime(DEFAULT_SERVER_DATE_FORMAT)
        # test sale
        self.create_simple_invoice(
            journal.id, date_invoice=date_yesterday, date=date_yesterday,
            type_invoice='out_invoice')
        invoice_2 = self.create_simple_invoice(journal.id, False, False, 'out_invoice')
        self.assertTrue((invoice_2.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_2.action_invoice_open()
        # test purchase
        self.create_simple_invoice(
            journal_purchase.id, date_invoice=date_yesterday, date=date_yesterday,
            type_invoice='in_invoice')
        invoice_3 = self.create_simple_invoice(
            journal_purchase.id, False, False, 'in_invoice')
        self.assertTrue((invoice_3.state == 'draft'),
                        "Initial invoice state is not Draft")
        with self.assertRaises(UserError):
            invoice_3.action_invoice_open()
