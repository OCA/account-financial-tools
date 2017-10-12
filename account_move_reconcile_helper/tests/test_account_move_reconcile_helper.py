# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAccountMoveReconcileHelper(TransactionCase):

    def setUp(self):
        super(TestAccountMoveReconcileHelper, self).setUp()
        self.AccountObj = self.env['account.account']
        self.AccountJournalObj = self.env['account.journal']
        self.AccountMoveObj = self.env['account.move']
        self.AccountMoveLineObj = self.env['account.move.line']

        self.account_type_recv = self.env.ref(
            'account.data_account_type_receivable')
        self.account_type_rev = self.env.ref(
            'account.data_account_type_revenue')

        self.account_recv = self.AccountObj.create({
            'code': 'MRH-RECVT',
            'name': "Receivable (test)",
            'reconcile': True,
            'user_type_id': self.account_type_recv.id,
        })
        self.account_sale = self.AccountObj.create({
            'code': 'MRH-SALET',
            'name': "Receivable (sale)",
            'reconcile': True,
            'user_type_id': self.account_type_rev.id,
        })

        self.sales_journal = self.AccountJournalObj.create({
            'name': "Sales journal",
            'code': 'MRH-SAJT',
            'type': 'sale',
            'default_credit_account_id': self.account_sale.id,
            'default_debit_account_id': self.account_sale.id,
        })

    def create_account_move(self, amount, debit_account, credit_account):
        return self.AccountMoveObj.create({
            'journal_id': self.sales_journal.id,
            'line_ids': [
                (0, 0, {
                    'name': "Receivable line",
                    'account_id': debit_account.id,
                    'debit': amount,
                }),
                (0, 0, {
                    'name': "Sales line",
                    'account_id': credit_account.id,
                    'credit': amount,
                }),
            ]
        })

    def test_01_partial_reconcile(self):
        base_move = self.create_account_move(
            5000, self.account_recv, self.account_sale)

        move1 = self.create_account_move(
            1000, self.account_sale, self.account_recv)

        move2 = self.create_account_move(
            1000, self.account_sale, self.account_recv)

        lines = self.AccountMoveLineObj.search([
            ('move_id', 'in', [base_move.id, move1.id, move2.id]),
            ('account_id', '=', self.account_recv.id)
        ])

        lines.reconcile()

        for line in lines:
            self.assertEquals(line.reconcile_line_ids, lines)

    def test_02_full_reconcile(self):
        base_move = self.create_account_move(
            5000, self.account_recv, self.account_sale)

        move2 = self.create_account_move(
            2500, self.account_sale, self.account_recv)
        move3 = self.create_account_move(
            2500, self.account_sale, self.account_recv)

        lines = self.AccountMoveLineObj.search([
            ('move_id', 'in', [base_move.id, move2.id, move3.id]),
            ('account_id', '=', self.account_recv.id)
        ])

        lines.reconcile()

        for line in lines:
            self.assertEquals(line.reconcile_line_ids, lines)
            self.assertEquals(
                line.full_reconcile_id.reconciled_line_ids,
                line.reconcile_line_ids)
