# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp.tests.common import TransactionCase
from openerp.exceptions import ValidationError


class TestAccountBlockAccount(TransactionCase):
    def test_account_block_account(self):
        invoice = self.env.ref('account.demo_invoice_0')
        invoice_line = self.env.ref(
            'account.demo_invoice_0_line_rpanrearpanelshe0'
        )
        invoice.account_id.blocked = True
        with self.assertRaises(ValidationError):
            invoice.write({
                'account_id': invoice.account_id.id,
            })
        invoice_line.account_id.blocked = True
        with self.assertRaises(ValidationError):
            invoice_line.write({
                'account_id': invoice_line.account_id.id,
            })
        with self.assertRaises(ValidationError):
            invoice_line.copy()
        with self.assertRaises(ValidationError):
            invoice.action_move_create()
