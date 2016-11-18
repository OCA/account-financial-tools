# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from datetime import date
from openerp import workflow
from openerp.tests import common


class TestAccountVoucher(common.TransactionCase):

    def setUp(self):
        super(TestAccountVoucher, self).setUp()
        self.env.user.company_id.disable_voucher_auto_lines = True
        year = datetime.now().year
        self.account = self.env['account.account'].search(
            [('type', '=', 'receivable'), ('currency_id', '=', False)],
            limit=1)[0]
        self.account_credit_run_model = self.env['credit.control.run']
        self.partner = self.env['res.partner'].create({
            'name': 'Test',
            'customer': True,
        })
        self.credit_control_policy = self.env.ref(
            'account_credit_control.credit_control_3_time')
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.account.id,
            'date_invoice': '%s-01-01' % year,
            'type': 'out_invoice',
            'origin': 'TEST1234',
            'invoice_line': [(0, 0, {
                'name': 'Test',
                'account_id': self.account.id,
                'price_unit': 234.56,
                'quantity': 1,
            })],
        })

        workflow.trg_validate(
            self.uid, 'account.invoice', self.invoice.id,
            'invoice_open', self.cr)

        self.voucher = self.env['account.voucher'].create({
            'date': '%s-01-02' % year,
            'name': "test voucher", 'amount': 11.00,
            'account_id': self.account.id,
            'partner_id': self.partner.id,
            'type': 'receipt',
        })

        voucher_data = self.voucher
        onchange_res = voucher_data.onchange_partner_id(
            voucher_data.partner_id.id, voucher_data.journal_id.id,
            voucher_data.amount, voucher_data.currency_id.id,
            voucher_data.type, voucher_data.date)

        lines = [(0, 0, line_data) for line_data in
                 onchange_res['value']['line_cr_ids']]
        self.voucher.write({'line_cr_ids': lines})

    def test_invoice_payment_and_credit_line(self):
        self.voucher.button_proforma_voucher()
        self.invoice.payment_ids.update({'date_maturity': date.today()})
        self.credit_control_policy.update(
            {'account_ids': [(4, self.account.id)]})
        self.credit = self.account_credit_run_model.create({
            'date': date.today()})
        self.credit.generate_credit_lines()
        self.credit.open_credit_lines()

        invoice_policy = self.env['credit.control.policy.changer'].create({
            'new_policy_id': self.credit_control_policy.id,
            'new_policy_level_id': self.credit_control_policy.level_ids[0].id,
            'move_line_ids': [(4, self.invoice.payment_ids.id)]})
        invoice_policy.set_new_policy()

        line_id = self.env['credit.control.line'].search(
            [('partner_id', '=', self.partner.id),
             ('policy_level_id', '=',
              self.credit_control_policy.level_ids[0].id)], limit=1)
        self.assertEqual(line_id.amount_due,
                         self.invoice.payment_ids.credit)
