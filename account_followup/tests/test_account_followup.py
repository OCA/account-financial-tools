# -*- coding: utf-8 -*-
import datetime

from openerp import tools
import openerp.tests.common as common


class TestAccountFollowup(common.SavepointCase):
    @classmethod
    def setUp(cls):
        super(TestAccountFollowup, cls).setUpClass()

        cls.wizard_obj = cls.env['account_followup.print']
        cls.company_id = cls.env.user.company_id
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Company',
            'email': 'test@localhost',
            'is_company': True,
        })
        cls.followup_id = cls.env.ref("account_followup.demo_followup1")
        cls.type_payable = cls.env.ref('account.data_account_type_payable')
        cls.type_liquidity = cls.env.ref('account.data_account_type_liquidity')
        cls.type_receivable = cls.env.ref(
            'account.data_account_type_receivable')
        cls.pay_account_id = cls.env['account.account'].create({
            'name': 'Test pay account',
            'code': '628001',
            'user_type_id': cls.type_payable.id,
            'reconcile': True,
        })
        cls.journal_id = cls.env['account.journal'].create({
            'name': 'Test Bank',
            'type': 'bank',
            'code': 'BNK68',
            'currency_id': cls.company_id.currency_id.id,
        })
        cls.account_id = cls.env['account.account'].create({
            'name': 'Test receivable account',
            'code': '430001',
            'user_type_id': cls.type_receivable.id,
            'reconcile': True,
        })

        cls.first_followup_line_id = \
            cls.env.ref("account_followup.demo_followup_line1").id
        cls.last_followup_line_id = \
            cls.env.ref("account_followup.demo_followup_line3").id
        cls.product_id = cls.env["product.product"].create({
            'name': 'Product test',
        })
        cls.invoice_id = cls.env['account.invoice'].create({
            'partner_id': cls.partner.id,
            'account_id': cls.account_id.id,
            'journal_id': cls.journal_id.id,
            'company_id': cls.company_id.id,
            'currency_id': cls.company_id.currency_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': "LCD Screen",
                    'product_id': cls.product_id.id,
                    'account_id': cls.pay_account_id.id,
                    'quantity': 5,
                    'price_unit': 200,
                })
            ]
        })
        cls.invoice_id.signal_workflow('invoice_open')
        cls.current_date = datetime.datetime.now()

    def test_00_send_followup_after_3_days(self):
        """ Send follow up after 3 days and check nothing is done (as first
        follow-up level is only after 15 days)"""
        delta = datetime.timedelta(days=3)
        result = self.current_date + delta
        self.wizard_id = self.wizard_obj.with_context(
            followup_id=self.followup_id).create({
                'date': result.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
                'followup_id': self.followup_id.id,
            })
        self.wizard_id.with_context(followup_id=self.followup_id).do_process()
        self.assertFalse(self.partner.latest_followup_level_id)

    def run_wizard_three_times(self):
        delta = datetime.timedelta(days=40)
        result = self.current_date + delta
        self.wizard_id = \
            self.wizard.with_context(followup_id=self.followup_id).create({
                'date': result.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
                'followup_id': self.followup_id
            })
        self.wizard.with_context(followup_id=self.followup_id).do_process(
            [self.wizard_id])
        self.wizard_id = \
            self.wizard.with_context(followup_id=self.followup_id).create({
                'date': result.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
                'followup_id': self.followup_id,
            })
        self.wizard.with_context(followup_id=self.followup_id).do_process(
            [self.wizard_id])
        self.wizard_id = \
            self.wizard.with_context(followup_id=self.followup_id).create({
                'date': result.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
                'followup_id': self.followup_id,
            })
        self.wizard.with_context(followup_id=self.followup_id).do_process(
            [self.wizard_id])

    def test_01_send_followup_later_for_upgrade(self):
        """ Send one follow-up after 15 days to check it upgrades to level 1"""
        delta = datetime.timedelta(days=15)
        result = self.current_date + delta
        self.wizard_id = \
            self.wizard.with_context(followup_id=self.followup_id).create({
                'date': result.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
                'followup_id': self.followup_id
            })
        self.wizard_id.with_context(followup_id=self.followup_id).do_process()
        self.assertEqual(
            self.partner.latest_followup_level_id.id,
            self.first_followup_line_id,
            "Not updated to the correct follow-up level")

    def test_02_check_manual_action(self):
        """ Check that when running the wizard three times that the manual
        action is set"""
        self.run_wizard_three_times()
        self.assertEqual(
            self.partner.payment_next_action,
            "Call the customer on the phone! ",
            "Manual action not set")
        self.assertEqual(
            self.partner.payment_next_action_date,
            self.current_date.strftime(tools.DEFAULT_SERVER_DATE_FORMAT))

    def test_03_filter_on_credit(self):
        """ Check the partners can be filtered on having credits """
        ids = self.env['res.partner'].search([
            ('payment_amount_due', '>', 0.0)
        ])
        self.assertIn([self.partner_id.id], ids)

    def test_04_action_done(self):
        """ Run the wizard 3 times, mark it as done, check the action fields
        are empty"""
        self.run_wizard_three_times()
        self.partner.action_done()
        self.assertFalse(self.partner.payment_next_action,
                         "Manual action not emptied")
        self.assertFalse(self.partner.payment_responsible_id)
        self.assertFalse(self.partner.payment_next_action_date)

    def test_05_litigation(self):
        """ Set the account move line as litigation, run the wizard 3 times
        and check nothing happened. Turn litigation off.  Run the wizard 3
        times and check it is in the right follow-up level.
        """
        aml_id = self.partner.unreconciled_aml_ids[0].id
        self.env['account.move.line'].write({'blocked': True})
        self.run_wizard_three_times()
        self.assertFalse(
            self.partner.latest_followup_level_id,
            "Litigation does not work")
        self.env['account.move.line'].write(aml_id, {'blocked': False})
        self.run_wizard_three_times()
        self.assertEqual(
            self.partner.latest_followup_level_id.id,
            self.last_followup_line_id,
            "Lines are not equal",
        )

    def test_06_pay_the_invoice(self):
        """Run wizard until manual action, pay the invoice and check that
        partner has no follow-up level anymore and after running the wizard
        the action is empty"""
        self.test_02_check_manual_action()
        delta = datetime.timedelta(days=1)
        result = self.current_date + delta
        self.invoice.pay_and_reconcile(
            self.journal_id, 1000.0,
            self.invoice.date_invoice,
            self.pay_account_id,
        )
        self.assertFalse(
            self.partner.latest_followup_level_id,
            "Level not empty")
        self.wizard_id = \
            self.wizard.with_context(followup_id=self.followup_id).create({
                'date': result.strftime(tools.DEFAULT_SERVER_DATE_FORMAT),
                'followup_id': self.followup_id
            })
        self.wizard_id.with_context(followup_id=self.followup_id).do_process()
        self.assertEqual(
            0, self.partner.payment_amount_due,
            "Amount Due != 0")
        self.assertFalse(
            self.partner.payment_next_action_date,
            "Next action date not cleared")
