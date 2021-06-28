# -*- coding: utf-8 -*-
# Copyright 2014 Stéphane Bidoul <stephane.bidoul@acsone.eu>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase


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

    def test_reverse_posted_reconcile(self):
        move = self._create_move()
        self.assertEqual(
            self._move_str(move), '0.00100.00:SALE_100.000.00:CUSTOMER_')
        rev = move.create_reversals(post=True, reconcile=True)
        self.assertEqual(len(rev), 1)
        self.assertEqual(
            self._move_str(rev), '100.000.00:SALE_0.00100.00:CUSTOMER_')
        reconciled_line = move.line_ids.filtered(
            lambda l: l.account_id.reconcile)
        self.assertEqual(
            'posted', rev.state)
        self.assertTrue(reconciled_line.full_reconcile_id)
