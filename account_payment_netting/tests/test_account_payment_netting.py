# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import SavepointCase, Form
from odoo.exceptions import UserError


class TestAccountNetting(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountNetting, cls).setUpClass()
        cls.invoice_model = cls.env['account.invoice']
        cls.payment_model = cls.env['account.payment']
        cls.register_payment_model = cls.env['account.register.payments']
        cls.account_receivable = cls.env['account.account'].create({
            'code': 'AR',
            'name': 'Account Receivable',
            'user_type_id': cls.env.ref(
                'account.data_account_type_receivable').id,
            'reconcile': True,
        })
        cls.account_payable = cls.env['account.account'].create({
            'code': 'AP',
            'name': 'Account Payable',
            'user_type_id': cls.env.ref(
                'account.data_account_type_payable').id,
            'reconcile': True,
        })
        cls.account_revenue = cls.env['account.account'].search([
            ('user_type_id', '=', cls.env.ref(
                'account.data_account_type_revenue').id)
        ], limit=1)
        cls.account_expense = cls.env['account.account'].search([
            ('user_type_id', '=', cls.env.ref(
                'account.data_account_type_expenses').id)
        ], limit=1)
        cls.partner1 = cls.env['res.partner'].create({
            'supplier': True,
            'customer': True,
            'name': 'Supplier/Customer 1',
            'property_account_receivable_id': cls.account_receivable.id,
            'property_account_payable_id': cls.account_payable.id,
        })
        cls.partner2 = cls.env['res.partner'].create({
            'supplier': True,
            'customer': True,
            'name': 'Supplier/Customer 2',
            'property_account_receivable_id': cls.account_receivable.id,
            'property_account_payable_id': cls.account_payable.id,
        })

        cls.sale_journal = cls.env['account.journal'].create({
            'name': 'Test sale journal',
            'type': 'sale',
            'code': 'INV',
        })
        cls.purchase_journal = cls.env['account.journal'].create({
            'name': 'Test expense journal',
            'type': 'purchase',
            'code': 'BIL',
        })
        cls.bank_journal = cls.env['account.journal'].create({
            'name': 'Test bank journal',
            'type': 'bank',
            'code': 'BNK',
        })
        cls.bank_journal.inbound_payment_method_ids |= cls.env.ref(
            'account.account_payment_method_manual_in')
        cls.bank_journal.outbound_payment_method_ids |= cls.env.ref(
            'account.account_payment_method_manual_out')

    def create_invoice(self, inv_type, partner, amount):
        """ Returns an open invoice """
        journal = inv_type == 'in_invoice' and \
            self.purchase_journal or self.sale_journal
        arap_account = inv_type == 'in_invoice' and \
            self.account_payable or self.account_receivable
        account = inv_type == 'in_invoice' and \
            self.account_expense or self.account_revenue
        invoice = self.invoice_model.create({
            'journal_id': journal.id,
            'type': inv_type,
            'partner_id': partner.id,
            'account_id': arap_account.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test',
                'price_unit': amount,
                'account_id': account.id,
            })],
        })
        return invoice

    def do_test_register_payment(self, invoices, expected_type, expected_diff):
        """ Test create customer/supplier invoices. Then, select all invoices
        and make neting payment. I expect:
        - Payment Type (inbound or outbound) = expected_type
        - Payment amont = expected_diff
        - Payment can link to all invoices
        - All 4 invoices are in paid status """
        # Select all invoices, and register payment
        ctx = {'active_ids': invoices.ids,
               'active_model': 'account.invoice'}
        view_id = 'account_payment_netting.view_account_payment_from_invoices'
        with Form(self.register_payment_model.with_context(ctx),
                  view=view_id) as f:
            f.journal_id = self.bank_journal
        payment_wizard = f.save()
        # Diff amount = expected_diff, payment_type = expected_type
        self.assertEqual(payment_wizard.amount, expected_diff)
        self.assertEqual(payment_wizard.payment_type, expected_type)
        # Create payments
        res = payment_wizard.create_payments()
        payment = self.payment_model.browse(res['res_id'])
        # Payment can link to all invoices
        self.assertEqual(set(payment.invoice_ids.ids), set(invoices.ids))
        invoices = self.invoice_model.browse(invoices.ids)
        # Test that all 4 invoices are paid
        self.assertEqual(list(set(invoices.mapped('state'))), ['paid'])

    def test_1_payment_netting_neutral(self):
        """ Test AR = AP """
        # Create 2 AR Invoice, total amount = 200.0
        ar_inv_p1_1 = self.create_invoice('out_invoice',  self.partner1, 100.0)
        ar_inv_p1_2 = self.create_invoice('out_invoice', self.partner1, 100.0)
        # Create 2 AP Invoice, total amount = 200.0
        ap_inv_p1_1 = self.create_invoice('in_invoice',  self.partner1, 100.0)
        ap_inv_p1_2 = self.create_invoice('in_invoice', self.partner1, 100.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_invoice_open()
        self.do_test_register_payment(invoices, 'outbound', 0.0)

    def test_2_payment_netting_inbound(self):
        """ Test AR > AP """
        # Create 2 AR Invoice, total amount = 200.0
        ar_inv_p1_1 = self.create_invoice('out_invoice',  self.partner1, 100.0)
        ar_inv_p1_2 = self.create_invoice('out_invoice', self.partner1, 100.0)
        # Create 2 AP Invoice, total amount = 160.0
        ap_inv_p1_1 = self.create_invoice('in_invoice',  self.partner1, 80.0)
        ap_inv_p1_2 = self.create_invoice('in_invoice', self.partner1, 80.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_invoice_open()
        self.do_test_register_payment(invoices, 'inbound', 40.0)

    def test_3_payment_netting_outbound(self):
        """ Test AR < AP """
        # Create 2 AR Invoice, total amount = 160.0
        ar_inv_p1_1 = self.create_invoice('out_invoice',  self.partner1, 80.0)
        ar_inv_p1_2 = self.create_invoice('out_invoice', self.partner1, 80.0)
        # Create 2 AP Invoice, total amount = 200.0
        ap_inv_p1_1 = self.create_invoice('in_invoice',  self.partner1, 100.0)
        ap_inv_p1_2 = self.create_invoice('in_invoice', self.partner1, 100.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p1_1 | ap_inv_p1_2
        invoices.action_invoice_open()
        self.do_test_register_payment(invoices, 'outbound', 40.0)

    def test_4_payment_netting_for_one_invoice(self):
        """ Test only 1 customer invoice, should also pass test """
        invoices = self.create_invoice('out_invoice',  self.partner1, 80.0)
        invoices.action_invoice_open()
        self.do_test_register_payment(invoices, 'inbound', 80.0)

    def test_5_payment_netting_wrong_partner_exception(self):
        """ Test when not invoices on same partner, show warning """
        # Create 2 AR Invoice, total amount = 160.0
        ar_inv_p1_1 = self.create_invoice('out_invoice',  self.partner1, 80.0)
        ar_inv_p1_2 = self.create_invoice('out_invoice', self.partner1, 80.0)
        # Create 1 AP Invoice, amount = 200.0, using different partner 2
        ap_inv_p2 = self.create_invoice('in_invoice',  self.partner2, 200.0)
        # Test Register Payment
        invoices = ar_inv_p1_1 | ar_inv_p1_2 | ap_inv_p2
        invoices.action_invoice_open()
        with self.assertRaises(UserError) as e:
            self.do_test_register_payment(invoices, 'outbound', 40.0)
        self.assertEqual(e.exception.name,
                         'All invoices must belong to same partner')
