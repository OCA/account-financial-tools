# Copyright 2015-2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime, timedelta

import odoo.tests.common as common
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class TestAccountConstraintChronology(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountConstraintChronology, cls).setUpClass()

        # Needed to create invoice

        cls.account_type1 = cls.env['account.account.type'].\
            create({'name': 'acc type test 1',
                    'type': 'receivable',
                    'include_initial_balance': True})
        cls.account_type2 = cls.env['account.account.type']. \
            create({'name': 'acc type test 2',
                    'type': 'other',
                    'include_initial_balance': True})
        cls.account_account = cls.env['account.account'].\
            create({'name': 'acc test',
                    'code': 'X2020',
                    'user_type_id': cls.account_type1.id,
                    'reconcile': True})
        cls.account_account_line = cls.env['account.account']. \
            create({'name': 'acc inv line test',
                    'code': 'X2021',
                    'user_type_id': cls.account_type2.id,
                    'reconcile': True})
        cls.sequence = cls.env['ir.sequence'].create(
            {'name': 'Journal Sale',
             'prefix': 'SALE', 'padding': 6,
             'company_id': cls.env.ref("base.main_company").id})
        cls.account_journal_sale = cls.env['account.journal']\
            .create({'name': 'Sale journal',
                     'code': 'SALE',
                     'type': 'sale',
                     'sequence_id': cls.sequence.id})
        cls.product = cls.env['product.product'].create(
            {'name': 'product name'})
        cls.analytic_account = cls.env['account.analytic.account'].\
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

    def test_invoice_draft_no_check(self):
        journal = self.get_journal_check(False)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date = yesterday.strftime(DEFAULT_SERVER_DATE_FORMAT)
        self.create_simple_invoice(journal.id, date)
        date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_2 = self.create_simple_invoice(journal.id, date)
        self.assertTrue((invoice_2.state == 'draft'),
                        "Initial invoice state is not Draft")
        self.assertTrue(invoice_2.action_invoice_open())

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

    def test_journal_change_type(self):
        self.account_journal_sale.check_chronology = True
        self.assertTrue(self.account_journal_sale.check_chronology)
        self.account_journal_sale.type = 'bank'
        self.account_journal_sale._onchange_type()
        self.assertFalse(self.account_journal_sale.check_chronology)

    def test_invoice_refund(self):
        journal = self.get_journal_check(True)
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        date_tomorrow = tomorrow.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice_1 = self.create_simple_invoice(journal.id, date_tomorrow)
        self.assertTrue(
            (invoice_1.state == "draft"), "Initial invoice state is not Draft"
        )
        invoice_1.action_invoice_open()
        date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        refund_invoice_wiz = (
            self.env["account.invoice.refund"]
            .with_context(active_ids=[invoice_1.id])
            .create(
                {
                    "description": "test_invoice_refund",
                    "filter_refund": "cancel",
                    "date": date,
                    "date_invoice": date,
                }
            )
        )
        with self.assertRaises(UserError):
            refund_invoice_wiz.invoice_refund()
        invoice_1.journal_id.refund_sequence = True
        refund_invoice_wiz.invoice_refund()
