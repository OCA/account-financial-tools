# Copyright 2020 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestAccountMoveLine(TransactionCase):

    def setUp(self):
        super().setUp()

        self.Account = self.env["account.account"]
        self.Move = self.env["account.move"]
        self.Journal = self.env["account.journal"]
        self.Tax = self.env["account.tax"]

    def constraint(self):
        account = self.Account.create({
            "code": "1",
            "name": "Account",
        })
        journal = self.Journal.create({
            "name": "Journal",
            "type": "sale",
            "code": "JOURNAL",
        })
        tax_1 = self.Tax.create({
            "name": "Tax 1",
            "amount": 15.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        })
        tax_2 = self.Tax.create({
            "name": "Tax 2",
            "amount": 15.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        })
        with self.assertRaises(ValidationError):
            self.Move.create({
                "journal_id": journal.id,
                "name": "Move",
                "date": "2020-11-01",
                "line_ids": [
                    (0, 0, {
                        "name": "Move Line",
                        "debit": 0.0,
                        "credit": 1000.0,
                        "account_id": account.id,
                        "tax_ids": [(6, 0, [tax_1, tax_2])],
                    }),
                ],
            })

    def nondestructive(self):
        account = self.Account.create({
            "code": "1",
            "name": "Account",
        })
        journal = self.Journal.create({
            "name": "Journal",
            "type": "sale",
            "code": "JOURNAL",
        })
        tax_1 = self.Tax.create({
            "name": "Tax 1",
            "amount": 15.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        })
        tax_2 = self.Tax.create({
            "name": "Tax 2",
            "amount": 15.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        })
        tax_3 = self.Tax.create({
            "name": "Tax 3",
            "amount": 15.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        })
        move = self.Move.with_context(skip_validate_single_tax=True).create({
            "journal_id": journal.id,
            "name": "Move",
            "date": "2020-11-01",
            "line_ids": [
                (0, 0, {
                    "name": "Move Line",
                    "debit": 0.0,
                    "credit": 1000.0,
                    "account_id": account.id,
                    "tax_ids": [(6, 0, [tax_1, tax_2])],
                }),
            ],
        })

        move.line_ids.tax_id = tax_2
        self.assertEqual(move.line_ids.tax_ids, (tax_1 | tax_2))

        with self.assertLogs() as logger_context:
            move.line_ids.tax_id = tax_3
        self.assertRegex(
            logger_context.output[0],
            r"Account Move Line #\d+ has more than one tax applied!"
        )
        self.assertEqual(move.line_ids.tax_ids, (tax_1 | tax_2 | tax_3))
