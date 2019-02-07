# -*- coding: utf-8 -*-
# Copyright 2014 Stéphane Bidoul <stephane.bidoul@acsone.eu>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from odoo.tests.common import TransactionCase
from odoo import fields
import random


class TestAccountReversal(TransactionCase):

    def setUp(self):
        super(TestAccountReversal, self).setUp()
        self.move_obj = self.env['account.move']
        self.move_line_obj = self.env['account.move.line']
        self.company_id = self.env.ref('base.main_company').id
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'COD',
            'type': 'sale',
            'company_id': self.company_id
        })
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        self.account_sale = self.env['account.account'].create({
            'name': 'Test sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
        })
        self.account_customer = self.env['account.account'].create({
            'name': 'Test customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })

    def _create_move(self, with_partner=True, amount=100):
        move_vals = {
            'journal_id': self.journal.id,
            'company_id': self.company_id,
            'line_ids': [(0, 0, {
                'name': '/',
                'debit': amount,
                'credit': 0,
                'account_id': self.account_customer.id,
                'company_id': self.company_id,
                'partner_id': with_partner and self.partner.id
            }), (0, 0, {
                'name': '/',
                'debit': 0,
                'credit': amount,
                'company_id': self.company_id,
                'account_id': self.account_sale.id,
            })]
        }
        return self.move_obj.create(move_vals)

    def _move_str(self, move):
        return ''.join(['%.2f%.2f%s' % (
            x.debit, x.credit, x.account_id == self.account_sale and
            ':SALE_' or ':CUSTOMER_')
            for x in move.line_ids.sorted(key=lambda r: r.account_id.id)])

    def test_reverse(self):
        move = self._create_move()
        self.assertEqual(
            self._move_str(move), '0.00100.00:SALE_100.000.00:CUSTOMER_')
        move_prefix = 'REV_TEST_MOVE:'
        line_prefix = 'REV_TEST_LINE:'
        rev = move.create_reversals(move_prefix=move_prefix,
                                    line_prefix=line_prefix, reconcile=True)
        self.assertEqual(len(rev), 1)
        self.assertEqual(rev.state, 'posted')
        self.assertEqual(
            self._move_str(rev), '100.000.00:SALE_0.00100.00:CUSTOMER_')
        self.assertEqual(rev.ref[0:len(move_prefix)], move_prefix)
        for line in rev.line_ids:
            self.assertEqual(line.name[0:len(line_prefix)], line_prefix)
            if line.account_id.reconcile:
                self.assertTrue(line.reconciled)

    def test_reverse_huge_move(self):

        move = self._create_move()

        for x in range(1, 100):
            amount = random.randint(10, 100) * x
            move.write({
                'line_ids': [(0, 0, {
                    'name': '/',
                    'debit': amount,
                    'credit': 0,
                    'account_id': self.account_customer.id,
                    'company_id': self.company_id,
                    'partner_id': self.partner.id
                }), (0, 0, {
                    'name': '/',
                    'debit': 0,
                    'credit': amount,
                    'company_id': self.company_id,
                    'account_id': self.account_sale.id,
                })]
            })
        self.assertEqual(len(move.line_ids), 200)

        move_prefix = 'REV_TEST_MOVE:'
        line_prefix = 'REV_TEST_LINE:'

        rev = move.create_reversals(move_prefix=move_prefix,
                                    line_prefix=line_prefix, reconcile=True)

        self.assertEqual(len(rev.line_ids), 200)
        self.assertEqual(rev.state, 'posted')

    def test_ignore_lock_date_check(self):
        """
        Test the reverse when the original move is locked by a lock date
        defined on the company.
        :return:
        """
        lock_date = fields.Date.today()
        # We can not specify lock dates if every moves are not locked
        self.move_obj.search([
            ('state', '!=', 'posted'),
            ('date', '<=', lock_date),
        ]).post()
        # We need access rights to reverse
        group_manager = self.env.ref("account.group_account_manager")
        self.env.user.write({
            'groups_id': [(4, group_manager.id, False)],
        })
        move = self._create_move()
        move.post()
        move.company_id.write({
            'period_lock_date': lock_date,
            'fiscalyear_lock_date': lock_date,
        })
        move_prefix = 'REV_TEST_MOVE:'
        line_prefix = 'REV_TEST_LINE:'
        # As the today date is locked, we have to specify another date
        future = fields.Date.from_string(lock_date) + timedelta(days=10)
        reverse_move = move.create_reversals(
            move_prefix=move_prefix, line_prefix=line_prefix, reconcile=True,
            date=fields.Date.to_string(future))
        # Ensure the reverse move is created
        self.assertTrue(reverse_move)
        self.assertEquals(reverse_move, move.reversal_id)
