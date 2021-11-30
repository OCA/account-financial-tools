# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common
from odoo import fields


class TestAccountMoveLineTaxEditable(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountMoveLineTaxEditable, cls).setUpClass()

        acc_obj = cls.env["account.account"]
        account100 = acc_obj.create(
            {
                "code": "100",
                "name": "Account 100",
                "user_type_id": cls.env.ref("account.data_account_type_receivable").id,
                "reconcile": True,
            }
        )
        account300 = acc_obj.create(
            {
                "code": "300",
                "name": "Account 300",
                "user_type_id": cls.env.ref(
                    "account.data_account_type_other_income"
                ).id,
            }
        )

        journal = cls.env["account.journal"].create(
            {"name": "Test journal", "type": "sale", "code": "TEST"}
        )
        move_vals = {
            "journal_id": journal.id,
            "name": "move test",
            "date": fields.Date.today(),
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "move test",
                        "debit": 0.0,
                        "credit": 1000.0,
                        "account_id": account300.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": "move test",
                        "debit": 1000.0,
                        "credit": 0.0,
                        "account_id": account100.id,
                    },
                ),
            ],
        }
        cls.move = cls.env["account.move"].create(move_vals)

    def test_compute_is_tax_editable(self):
        self.assertEqual(self.move.line_ids.mapped("is_tax_editable"), [True, True])
        self.move.post()
        self.assertEqual(self.move.line_ids.mapped("is_tax_editable"), [False, False])
