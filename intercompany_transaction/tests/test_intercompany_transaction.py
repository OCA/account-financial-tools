# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestIntercompanyTransaction(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_data_2 = cls.setup_other_company(name="Company B")
        cls.company_b = cls.company_data_2["company"]
        cls.ic_config = cls.env["intercompany.transaction.config"].create(
            {
                "from_company_id": cls.company_data["company"].id,
                "from_company_debit_account_id": cls.company_data[
                    "default_account_receivable"
                ].id,
                "to_company_id": cls.company_b.id,
                "to_company_debit_account_id": cls.company_data_2[
                    "default_account_receivable"
                ].id,
                "to_company_credit_account_id": cls.company_data_2[
                    "default_account_revenue"
                ].id,
                "to_company_journal_id": cls.company_data_2["default_journal_misc"].id,
            }
        )

    def test_01_intercompany_entry_creation(self):
        """Test that posting a move in Company A creates a draft move in Company B."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2024-01-01",
                "journal_id": self.company_data["default_journal_misc"].id,
                "is_intercompany_journal_entry": True,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Transfer line",
                            "account_id": self.company_data[
                                "default_account_receivable"
                            ].id,
                            "debit": 100.0,
                            "credit": 0.0,
                            "transfer_to_company_id": self.company_b.id,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Counterpart line",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                            "debit": 0.0,
                            "credit": 100.0,
                        }
                    ),
                ],
            }
        )
        move.action_post()

        # Check that a related move was created in Company B
        related_move = (
            self.env["account.move"]
            .sudo()
            .search(
                [
                    ("intercompany_source_account_move_id", "=", move.id),
                    ("company_id", "=", self.company_b.id),
                ]
            )
        )
        self.assertTrue(related_move, "Related move should be created in Company B")
        self.assertEqual(
            related_move.state, "draft", "Related move should be in draft state"
        )
        self.assertEqual(
            len(related_move.line_ids), 2, "Related move should have 2 lines"
        )

        # Check line values in Company B
        debit_line = related_move.line_ids.filtered(lambda line: line.debit > 0)
        credit_line = related_move.line_ids.filtered(lambda line: line.credit > 0)

        self.assertEqual(
            debit_line.account_id, self.ic_config.to_company_debit_account_id
        )
        self.assertEqual(
            credit_line.account_id, self.ic_config.to_company_credit_account_id
        )
        self.assertEqual(debit_line.debit, 100.0)
        self.assertEqual(credit_line.credit, 100.0)

    def test_02_intercompany_cancellation(self):
        """Test that drafting the source move cancels the related move."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.company_data["default_journal_misc"].id,
                "is_intercompany_journal_entry": True,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Transfer line",
                            "account_id": self.company_data[
                                "default_account_receivable"
                            ].id,
                            "debit": 100.0,
                            "transfer_to_company_id": self.company_b.id,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Counterpart",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                            "credit": 100.0,
                        }
                    ),
                ],
            }
        )
        move.action_post()

        related_move = (
            self.env["account.move"]
            .sudo()
            .search([("intercompany_source_account_move_id", "=", move.id)])
        )
        self.assertEqual(related_move.state, "draft")

        # Draft source move
        move.button_draft()
        self.assertEqual(
            related_move.state, "cancel", "Related move should be canceled"
        )

    def test_03_posted_linked_entry_restriction(self):
        """Test that we cannot draft the source move if the related move is posted."""
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.company_data["default_journal_misc"].id,
                "is_intercompany_journal_entry": True,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Transfer line",
                            "account_id": self.company_data[
                                "default_account_receivable"
                            ].id,
                            "debit": 100.0,
                            "transfer_to_company_id": self.company_b.id,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Counterpart",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                            "credit": 100.0,
                        }
                    ),
                ],
            }
        )
        move.action_post()

        related_move = (
            self.env["account.move"]
            .sudo()
            .search([("intercompany_source_account_move_id", "=", move.id)])
        )
        # Post the related move in Company B
        related_move.action_post()

        # Try to draft source move
        with self.assertRaisesRegex(
            ValidationError, "linked intercompany journal entry.*is already posted"
        ):
            move.button_draft()

    def test_04_validation_checks(self):
        """Test various validation constraints."""
        # Setup a valid base entry for testing field-level validations
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.company_data["default_journal_misc"].id,
                "is_intercompany_journal_entry": True,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Transfer line",
                            "account_id": self.company_data[
                                "default_account_receivable"
                            ].id,
                            "debit": 100.0,
                            "transfer_to_company_id": self.company_b.id,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Counterpart",
                            "account_id": self.company_data[
                                "default_account_revenue"
                            ].id,
                            "credit": 100.0,
                        }
                    ),
                ],
            }
        )
        line = move.line_ids.filtered(lambda line: line.transfer_to_company_id)

        # 1. Type must be 'entry'
        move.move_type = "out_invoice"
        with self.assertRaisesRegex(ValidationError, "Type' must be 'Journal Entry'"):
            line._get_move_line_intercompany_transaction_config()
        move.move_type = "entry"

        # 2. Config must exist
        company_c = self.setup_other_company(name="Company C")["company"]
        line.transfer_to_company_id = company_c
        with self.assertRaisesRegex(
            ValidationError, "Intercompany Transaction Configuration Not Found"
        ):
            line._get_move_line_intercompany_transaction_config()
        line.transfer_to_company_id = self.company_b

        # 3. Correct account for configuration
        line.account_id = self.company_data["default_account_payable"]
        with self.assertRaisesRegex(
            ValidationError, "Intercompany Account Configuration"
        ):
            line._get_move_line_intercompany_transaction_config()
        line.account_id = self.company_data["default_account_receivable"]

        # 4. is_intercompany_journal_entry must be True
        move.is_intercompany_journal_entry = False
        with self.assertRaisesRegex(
            ValidationError, "can only be set for Intercompany Transaction"
        ):
            line._get_move_line_intercompany_transaction_config()
        move.is_intercompany_journal_entry = True
