# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common
from odoo.exceptions import UserError


class TestAccountFxSpot(common.TransactionCase):
    def setUp(self):
        super(TestAccountFxSpot, self).setUp()
        self.fx_spot_obj = self.env["account.fx.spot"]
        self.payment_wiz_obj = self.env["account.fx.spot.payment"]
        self.journal_obj = self.env["account.journal"]
        self.account_obj = self.env["account.account"]

        self.company = self.env.ref('base.main_company')
        self.test_partner = self.env["res.partner"].create({
            "name": "Test Partner"
        })
        self.curr1, self.curr2 = self.get_testing_currencies(self.company)
        # Create a Journal and a default account for currencies 1, 2 and
        # company's.
        self.payment_journals = dict()
        user_type_id = self.env.ref("account.data_account_type_liquidity")
        acc_curr_c = self.account_obj.create({
            "code": 99999,
            "name": "Bank company currency Test",
            "user_type_id": user_type_id.id,
            "currency_id": self.company.currency_id.id,
        })
        self.payment_journals[
            self.company.currency_id.id] = self.journal_obj.create({
                "name": "Journal Company Currency Test",
                "code": "TESTC",
                "type": "bank",
                "currency_id": self.company.currency_id.id,
                "default_debit_account_id": acc_curr_c.id,
                "default_credit_account_id": acc_curr_c.id,
            })
        acc_curr1 = self.account_obj.create({
            "code": 99998,
            "name": "Bank 1 Test",
            "user_type_id": user_type_id.id,
            "currency_id": self.curr1.id,
        })
        self.payment_journals[self.curr1.id] = self.journal_obj.create({
            "name": "Journal 1 Test",
            "code": "TEST1",
            "type": "bank",
            "currency_id": self.curr1.id,
            "default_debit_account_id": acc_curr1.id,
            "default_credit_account_id": acc_curr1.id,
        })
        acc_curr2 = self.account_obj.create({
            "code": 99997,
            "name": "Bank 2 Test",
            "user_type_id": user_type_id.id,
            "currency_id": self.curr2.id,
        })
        self.payment_journals[self.curr2.id] = self.journal_obj.create({
            "name": "Journal 2 Test",
            "code": "TEST2",
            "type": "bank",
            "currency_id": self.curr2.id,
            "default_debit_account_id": acc_curr2.id,
            "default_credit_account_id": acc_curr2.id,
        })

        # Get payments methods:
        self.payment_methods = {
            'inbound': self.env.ref(
                'account.account_payment_method_manual_in'),
            'outbound': self.env.ref(
                'account.account_payment_method_manual_out'),
        }

    def get_testing_currencies(self, company):
        currencies = self.env["res.currency"].search(
            [("id", "!=", company.currency_id.id)], limit=2)
        if len(currencies) == 2:
            return currencies[0], currencies[1]
        currency1 = self.env.ref("base.CAD")
        currency2 = self.env.ref("base.BRL")
        if currency1 == company.currency_id:
            currency1 = self.env.ref("base.DKK")
        elif currency2 == company.currency_id:
            currency2 = self.env.ref("base.DKK")
        return currency1, currency2

    def do_payment(self, transaction, payment_type, amount):
        if payment_type == "outbound":
            journal = self.payment_journals.get(transaction.out_currency_id.id)
            payment_method = self.payment_methods.get("outbound")
            partner_type = "supplier"
        else:
            journal = self.payment_journals.get(transaction.in_currency_id.id)
            payment_method = self.payment_methods.get("inbound")
            partner_type = "customer"
        vals = {
            "payment_type": payment_type,
            "partner_type": partner_type,
            "journal_id": journal.id,
            "currency_id": journal.currency_id.id,
            "amount": amount,
            "payment_method_id": payment_method.id,
        }
        return self.payment_wiz_obj.with_context(
            active_ids=transaction.ids).create(vals)

    def test_01_company_currency_out(self):
        """Test workflow with the company currency as outgoing currency."""
        transaction = self.fx_spot_obj.create({
            "partner_id": self.test_partner.id,
            "amount_out": 100.0,
            "out_currency_id": self.company.currency_id.id,
            "rate": 1.5,
            "amount_in": 150.0,
            "in_currency_id": self.curr1.id,
        })
        # Test onchange methods:
        transaction._onchange_amounts()
        self.assertEqual(transaction.rate, 1.5)
        transaction._onchange_rate()
        self.assertEqual(transaction.amount_in, 150.0)
        # Test error raise:
        with self.assertRaises(UserError):
            transaction.action_done()
        # test cancellation and resetting to draft:
        with self.assertRaises(UserError):
            transaction.action_draft()
        transaction.action_cancel()
        date = transaction.date_transaction
        transaction.action_draft()
        transaction.date_transaction = date
        # test confirmation and payment workflow:
        transaction.action_confirm()
        self.assertTrue(transaction.move_id)
        self.assertFalse(transaction.reconciled)
        pay_out_1 = self.do_payment(transaction, "outbound", 75.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_out, 25.0)
        pay_out_1 = self.do_payment(transaction, "outbound", 25.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_out, 0.0)
        pay_out_1 = self.do_payment(transaction, "inbound", 100.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_in, 50.0)
        # Test errors raise:
        with self.assertRaises(UserError):
            transaction.action_cancel()
        with self.assertRaises(UserError):
            transaction.action_done()
        with self.assertRaises(UserError):
            transaction.action_re_open()
        # End workflow/reconcilation:
        pay_out_1 = self.do_payment(transaction, "inbound", 50.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_in, 0.0)
        self.assertTrue(transaction.reconciled)
        self.assertEqual(transaction.state, 'done')
        with self.assertRaises(UserError):
            transaction.action_cancel()
        # Check payments:
        action = transaction.action_view_payments()
        self.assertTrue(action)
        self.assertEqual(transaction.payments_count, 4)
        self.assertTrue(transaction.payment_ids[0].has_fx_spots)
        action = transaction.payment_ids[0].button_fx_spot()
        self.assertTrue(action)

    def test_02_company_currency_in(self):
        """Test workflow with the company currency as incoming currency."""
        transaction = self.fx_spot_obj.create({
            "partner_id": self.test_partner.id,
            "amount_out": 100.0,
            "out_currency_id":  self.curr2.id,
            "rate": 1.5,
            "amount_in": 150.0,
            "in_currency_id": self.company.currency_id.id,
        })
        transaction.action_confirm()
        self.assertTrue(transaction.move_id)
        self.assertFalse(transaction.reconciled)
        pay_out_1 = self.do_payment(transaction, "outbound", 75.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_out, 25.0)
        pay_out_1 = self.do_payment(transaction, "outbound", 25.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_out, 0.0)
        pay_out_1 = self.do_payment(transaction, "inbound", 100.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_in, 50.0)
        pay_out_1 = self.do_payment(transaction, "inbound", 50.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_in, 0.0)
        self.assertTrue(transaction.reconciled)

    def test_03_no_company_currency(self):
        """Test workflow with two non-company currencies."""
        transaction = self.fx_spot_obj.create({
            "partner_id": self.test_partner.id,
            "amount_out": 100.0,
            "out_currency_id":  self.curr2.id,
            "rate": 1.5,
            "amount_in": 150.0,
            "in_currency_id": self.curr1.id,
        })
        transaction.action_confirm()
        self.assertTrue(transaction.move_id)
        self.assertFalse(transaction.reconciled)
        pay_out_1 = self.do_payment(transaction, "outbound", 75.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_out, 25.0)
        pay_out_1 = self.do_payment(transaction, "outbound", 25.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_out, 0.0)
        pay_out_1 = self.do_payment(transaction, "inbound", 100.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_in, 50.0)
        pay_out_1 = self.do_payment(transaction, "inbound", 50.0)
        pay_out_1.create_payments()
        self.assertAlmostEquals(transaction.residual_in, 0.0)
        self.assertTrue(transaction.reconciled)

    def test_04_group_payments(self):
        """Test payment wizard with several transactions."""
        t1 = self.fx_spot_obj.create({
            "partner_id": self.test_partner.id,
            "amount_out": 100.0,
            "out_currency_id": self.company.currency_id.id,
            "rate": 1.5,
            "amount_in": 150.0,
            "in_currency_id": self.curr1.id,
        })
        t2 = self.fx_spot_obj.create({
            "partner_id": self.test_partner.id,
            "amount_out": 100.0,
            "out_currency_id":  self.curr2.id,
            "rate": 1.5,
            "amount_in": 150.0,
            "in_currency_id": self.company.currency_id.id,
        })
        t3 = self.fx_spot_obj.create({
            "partner_id": self.test_partner.id,
            "amount_out": 100.0,
            "out_currency_id":  self.curr2.id,
            "rate": 1.5,
            "amount_in": 150.0,
            "in_currency_id": self.curr1.id,
        })
        with self.assertRaises(UserError):
            # Transactions aren't open:
            self.do_payment(t1, "outbound", 50.0)
        (t1 + t2 + t3).action_confirm()
        # Check common inbound currency:
        payment = self.do_payment(t1, "inbound", 50.0)
        common_in = payment.with_context(active_ids=(t1 + t3).ids)
        self.assertEqual(common_in.default_type(), 'inbound')
        res = common_in.default_get(['multi', 'payment_type'])
        self.assertEqual(res.get('amount', 0.0), 300.0)
        common_in.onchange_payment_type()
        self.assertEqual(common_in.amount, 300.0)
        # Check common outbound currency:
        payment = self.do_payment(t2, "outbound", 50.0)
        common_out = payment.with_context(active_ids=(t2 + t3).ids)
        self.assertEqual(common_out.default_type(), 'outbound')
        res = common_out.default_get(['multi', 'payment_type'])
        self.assertEqual(res.get('amount', 0.0), 200.0)
        common_out.onchange_payment_type()
        self.assertEqual(common_out.amount, 200.0)
