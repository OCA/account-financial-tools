# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo.tests.common as common
from odoo import fields


class TestAccountMoveLineTaxEditable(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
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
                        "name": "move test line 1",
                        "debit": 0.0,
                        "credit": 1000.0,
                        "account_id": account300.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": "move test line 2",
                        "debit": 1000.0,
                        "credit": 0.0,
                        "account_id": account100.id,
                    },
                ),
            ],
        }
        cls.move = cls.env["account.move"].create(move_vals)
        cls.tax15 = cls.env["account.tax"].create(
            {
                "name": "Test tax 15",
                "amount": 15,
            }
        )

    def test_compute_is_tax_editable(self):
        self.assertEqual(self.move.line_ids.mapped("is_tax_editable"), [True, True])
        self.move.action_post()
        self.assertEqual(self.move.line_ids.mapped("is_tax_editable"), [False, False])

    def test_tax_edited(self):
        line1 = self.move.line_ids[0]
        line1.tax_line_id = self.tax15.id
        line2 = self.move.line_ids[1]
        self.move.action_post()
        self.assertEqual(line1.tax_line_id.id, self.tax15.id)
        self.assertEqual(line2.tax_line_id.id, False)
        self.assertEqual(line1.tax_repartition_line_id.tax_id.id, self.tax15.id)

    def test_tax_not_edited(self):
        """In this case we set the tax_repartition_line_id field, simulating that the
        move came from an invoice with tax applied. Thus, tax_line_id should be computed"""
        line1 = self.move.line_ids[1]
        line1.tax_repartition_line_id = self.tax15.invoice_repartition_line_ids[1]
        self.assertEqual(line1.tax_line_id.id, self.tax15.id)
