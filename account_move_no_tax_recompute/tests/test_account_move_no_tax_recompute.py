from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMoveNoTaxRecompute(AccountTestInvoicingCommon):
    def _create_entry_with_tax(self):
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.today(),
                "journal_id": self.company_data["default_journal_misc"].id,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Base",
                            "account_id": self.company_data[
                                "default_account_expense"
                            ].id,
                            "debit": 100.0,
                            "credit": 0.0,
                            "tax_ids": [Command.set(self.tax_purchase_a.ids)],
                        }
                    ),
                    Command.create(
                        {
                            "name": "Counterpart",
                            "account_id": self.company_data[
                                "default_account_payable"
                            ].id,
                            "debit": 0.0,
                            "credit": 100.0,
                        }
                    ),
                ],
            }
        )

        base_line = move.line_ids.filtered(lambda line: line.tax_ids)[:1]
        tax_line = move.line_ids.filtered("tax_repartition_line_id")[:1]
        counterpart_line = (move.line_ids - base_line - tax_line)[:1]

        self.assertTrue(base_line, "A base line with taxes is expected")
        self.assertTrue(tax_line, "A tax line should be dynamically created")
        self.assertTrue(counterpart_line, "A counterpart line is expected")

        return move, base_line, tax_line, counterpart_line

    def _get_tax_balance_total(self, move):
        return sum(move.line_ids.filtered("tax_repartition_line_id").mapped("balance"))

    def _create_alternative_purchase_tax(self):
        alt_amount = (
            self.tax_purchase_a.amount / 2.0 if self.tax_purchase_a.amount else 5.0
        )
        return self.tax_purchase_a.copy(
            {
                "name": "Alt Purchase Tax",
                "amount": alt_amount,
            }
        )

    def test_entry_recomputes_tax_lines_by_default(self):
        move, base_line, tax_line, counterpart_line = self._create_entry_with_tax()
        initial_tax_balance = self._get_tax_balance_total(move)
        alt_tax = self._create_alternative_purchase_tax()

        move.write(
            {
                "line_ids": [
                    Command.update(
                        base_line.id, {"tax_ids": [Command.set(alt_tax.ids)]}
                    ),
                ]
            }
        )

        move.invalidate_recordset(["line_ids"])
        self.assertNotEqual(
            self._get_tax_balance_total(move),
            initial_tax_balance,
            "Tax line should be recomputed on a regular journal entry write.",
        )

    def test_entry_keeps_tax_lines_when_no_tax_recompute(self):
        move, base_line, tax_line, counterpart_line = self._create_entry_with_tax()
        initial_tax_balance = self._get_tax_balance_total(move)
        alt_tax = self._create_alternative_purchase_tax()
        move.no_tax_recompute = True

        move.write(
            {
                "line_ids": [
                    Command.update(
                        base_line.id, {"tax_ids": [Command.set(alt_tax.ids)]}
                    ),
                ]
            }
        )

        move.invalidate_recordset(["line_ids"])
        self.assertEqual(
            self._get_tax_balance_total(move),
            initial_tax_balance,
            "Tax line should stay unchanged when no_tax_recompute is enabled.",
        )

    def test_duplicate_entry_keeps_no_tax_recompute_without_tax_sync(self):
        move, base_line, tax_line, counterpart_line = self._create_entry_with_tax()
        move.no_tax_recompute = True

        duplicated_move = move.copy()

        self.assertTrue(
            duplicated_move.no_tax_recompute,
            "Duplicated journal entry should keep no_tax_recompute enabled.",
        )
        self.assertEqual(
            len(duplicated_move.line_ids),
            len(move.line_ids),
            "Duplicating a frozen journal entry should not create extra tax lines.",
        )
