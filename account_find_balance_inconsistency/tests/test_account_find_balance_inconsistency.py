# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountFindBalanceInconsistency(TransactionCase):
    def test_account_find_balance_inconsistency(self):
        wizard = self.env['account.find.balance.inconsistency'].create({})
        # raises a warning when everything's fine
        with self.assertRaises(UserError):
            wizard.check_report()
        # shows move lines otherwise
        move_line = self.env['account.move.line'].search([], limit=1)
        self.env.cr.execute(
            'update account_move_line set credit=0, debit=0 where id=%s',
            (move_line.id,),
        )
        action = wizard.check_report()
        self.assertIn(
            move_line,
            self.env['account.move.line'].search(action['domain']),
        )
