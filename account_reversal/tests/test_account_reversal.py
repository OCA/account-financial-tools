# Copyright 2014 Stéphane Bidoul <stephane.bidoul@acsone.eu>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import random

from odoo.tests import Form
from odoo.tests.common import TransactionCase

from odoo.addons.account_reversal.models.account_move import (
    MoveAlreadyReversedValidationError,
)


class TestAccountReversal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.move_obj = cls.env["account.move"]
        cls.move_line_obj = cls.env["account.move.line"]
        cls.reversal_obj = cls.env["account.move.reversal"]
        cls.company_id = cls.env.ref("base.main_company").id
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test journal",
                "code": "COD",
                "type": "sale",
                "company_id": cls.company_id,
            }
        )

        cls.account_sale = cls.env["account.account"].create(
            {"name": "Test sale", "code": "700", "account_type": "income"}
        )
        cls.account_customer = cls.env["account.account"].create(
            {
                "name": "Test customer",
                "code": "430",
                "account_type": "expense",
                "reconcile": True,
            }
        )

    def _create_move(self, with_partner=True, amount=100):
        move_vals = {
            "journal_id": self.journal.id,
            "company_id": self.company_id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "/",
                        "debit": amount,
                        "credit": 0,
                        "account_id": self.account_customer.id,
                        "company_id": self.company_id,
                        "partner_id": with_partner and self.partner.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": "/",
                        "debit": 0,
                        "credit": amount,
                        "company_id": self.company_id,
                        "account_id": self.account_sale.id,
                    },
                ),
            ],
        }
        return self.move_obj.create(move_vals)

    def _move_str(self, move):
        return "".join(
            [
                "%.2f%.2f%s"
                % (
                    x.debit,
                    x.credit,
                    x.account_id == self.account_sale and ":SALE_" or ":CUSTOMER_",
                )
                for x in move.line_ids.sorted(key=lambda r: r.account_id.id)
            ]
        )

    def test_reverse(self):
        move = self._create_move()
        self.assertEqual(self._move_str(move), "0.00100.00:SALE_100.000.00:CUSTOMER_")
        move.to_be_reversed = True
        move._post()

        line_reason = "REV_TEST_LINE"

        with Form(
            self.reversal_obj.with_context(
                active_ids=move.ids, active_model="account.move"
            )
        ) as wizard_form:
            wizard_form.line_reason = line_reason
        wizard = wizard_form.save()
        action = wizard.reverse_moves()
        reversal_move = self.move_obj.browse(action.get("res_id"))
        self.assertEqual(len(reversal_move), 1)
        self.assertEqual(reversal_move.state, "posted")
        self.assertEqual(
            self._move_str(reversal_move), "100.000.00:SALE_0.00100.00:CUSTOMER_"
        )
        for line in reversal_move.line_ids:
            self.assertEqual(line.name[0 : len(line_reason)], line_reason)
            if line.account_id.reconcile:
                self.assertTrue(line.reconciled)
        self.assertFalse(move.to_be_reversed)

    def test_reverse_huge_move(self):

        move = self._create_move()

        for x in range(1, 100):
            amount = random.randint(10, 100) * x
            move.write(
                {
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "/",
                                "debit": amount,
                                "credit": 0,
                                "account_id": self.account_customer.id,
                                "company_id": self.company_id,
                                "partner_id": self.partner.id,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "/",
                                "debit": 0,
                                "credit": amount,
                                "company_id": self.company_id,
                                "account_id": self.account_sale.id,
                            },
                        ),
                    ]
                }
            )
        move._post()
        self.assertEqual(len(move.line_ids), 200)

        wizard_form = Form(
            self.reversal_obj.with_context(
                active_ids=move.ids, active_model="account.move"
            )
        )
        wizard = wizard_form.save()
        action = wizard.reverse_moves()
        reversal_move = self.move_obj.browse(action.get("res_id"))

        self.assertEqual(len(reversal_move.line_ids), 200)
        self.assertEqual(reversal_move.state, "posted")

    def test_already_reversed_constraint(self):
        account_move = self._create_move()
        account_move.action_post()
        account_move.to_be_reversed = True
        reversed_account_move = account_move._reverse_moves()
        self.assertEqual(account_move.reversal_id, reversed_account_move)
        self.assertFalse(account_move.to_be_reversed)
        with self.assertRaises(MoveAlreadyReversedValidationError), self.cr.savepoint():
            account_move.to_be_reversed = True
        # Cancelled reverse moves are not taken into account in reversal_id and the constraint
        # on to_be_reversed.
        reversed_account_move.button_cancel()
        self.assertFalse(account_move.reversal_id)
        account_move.to_be_reversed = True
