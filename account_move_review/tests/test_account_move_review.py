# Copyright 2026 Saad Elbahi
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMoveReview(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.grp_reviewer = cls.env.ref(
            "account_move_review.group_account_move_reviewer"
        )
        cls.grp_manager = cls.env.ref("account.group_account_manager")
        cls.grp_user = cls.env.ref("base.group_user")

        cls.accountant = cls.env["res.users"].create(
            {
                "name": "Review Test Accountant",
                "login": "review_test_accountant",
                "groups_id": [(6, 0, [cls.grp_user.id, cls.grp_manager.id])],
                "company_id": cls.company.id,
                "company_ids": [(6, 0, [cls.company.id])],
            }
        )
        cls.reviewer = cls.env["res.users"].create(
            {
                "name": "Review Test Reviewer",
                "login": "review_test_reviewer",
                "groups_id": [(6, 0, [cls.grp_user.id, cls.grp_reviewer.id])],
                "company_id": cls.company.id,
                "company_ids": [(6, 0, [cls.company.id])],
            }
        )
        cls.journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "general")],
            limit=1,
        )
        cls.accounts = cls.env["account.account"].search(
            [("company_ids", "in", [cls.company.id])],
            limit=2,
        )

    def _create_posted_move(self, user):
        move = (
            self.env["account.move"]
            .with_user(user)
            .create(
                {
                    "journal_id": self.journal.id,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "account_id": self.accounts[0].id,
                                "name": "Debit",
                                "debit": 100.0,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "account_id": self.accounts[1].id,
                                "name": "Credit",
                                "credit": 100.0,
                            },
                        ),
                    ],
                }
            )
        )
        move.with_user(user).action_post()
        return move

    def test_security_group_independence(self):
        self.assertIn(self.grp_manager, self.grp_reviewer.implied_ids)
        self.assertNotIn(self.grp_reviewer, self.grp_manager.implied_ids)
        self.assertNotIn(
            self.grp_reviewer, self.env.ref("base.group_system").implied_ids
        )
        self.assertTrue(self.reviewer.has_group("account.group_account_manager"))
        self.assertFalse(
            self.accountant.has_group("account_move_review.group_account_move_reviewer")
        )

    def test_default_compatibility_without_restriction(self):
        self.assertFalse(self.company.restrict_move_draft_to_reviewers)
        move = self._create_posted_move(self.accountant)
        move.with_user(self.accountant).button_draft()
        self.assertEqual(move.state, "draft")

        bank_journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "in", ("bank", "cash"))],
            limit=1,
        )
        partner = self.env["res.partner"].create({"name": "Compat Test Partner"})
        payment = (
            self.env["account.payment"]
            .with_user(self.accountant)
            .create(
                {
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": partner.id,
                    "amount": 25.0,
                    "journal_id": bank_journal.id,
                }
            )
        )
        payment.with_user(self.accountant).action_post()
        payment.with_user(self.accountant).action_draft()
        self.assertEqual(payment.state, "draft")

    def test_review_workflow_and_draft_guard(self):
        settings = self.env["res.config.settings"].create(
            {"restrict_move_draft_to_reviewers": True}
        )
        settings.execute()
        self.assertTrue(self.company.restrict_move_draft_to_reviewers)

        move = self._create_posted_move(self.accountant)
        self.assertEqual(move.review_state, "not_reviewed")
        self.assertFalse(move.document_type)

        # Document type can be updated after posting by regular accountants
        move.with_user(self.accountant).write({"document_type": "documentary"})
        self.assertEqual(
            set(move.line_ids.mapped("move_document_type")), {"documentary"}
        )

        # Non-reviewer blocked from draft reset and review actions
        with self.assertRaises(AccessError):
            move.with_user(self.accountant).button_draft()
        with self.assertRaises(AccessError):
            move.with_user(self.accountant).action_mark_reviewed()
        with self.assertRaises(AccessError):
            move.with_user(self.accountant).action_open_reset_draft_wizard()

        # Reviewer one-click review produces zero chatter messages
        msg_count = len(move.message_ids)
        move.with_user(self.reviewer).action_mark_reviewed()
        self.assertEqual(move.review_state, "reviewed")
        self.assertEqual(move.reviewed_by_id, self.reviewer)
        self.assertEqual(set(move.line_ids.mapped("move_review_state")), {"reviewed"})
        self.assertEqual(len(move.message_ids), msg_count)

        # Reviewer resets reviewed entry to draft via wizard with notes
        action = move.with_user(self.reviewer).action_open_reset_draft_wizard()
        self.assertEqual(
            action["context"]["default_recipient_user_id"], self.accountant.id
        )
        wizard = (
            self.env["account.move.review.wizard"]
            .with_user(self.reviewer)
            .with_context(**action["context"])
            .create({"notes": "Check cost center"})
        )
        wizard.action_confirm_reset_to_draft()

        self.assertEqual(move.state, "draft")
        self.assertEqual(move.review_state, "returned")
        self.assertEqual(move.review_notes, "Check cost center")
        self.assertFalse(move.activity_ids)
        self.assertIn(self.accountant.partner_id, move.message_ids[:1].partner_ids)

        # Re-posting returns move to not_reviewed
        move.with_user(self.accountant).action_post()
        self.assertEqual(move.review_state, "not_reviewed")
        self.assertEqual(
            set(move.line_ids.mapped("move_review_state")), {"not_reviewed"}
        )

        # Calling mark_reviewed twice is idempotent; direct button_draft resets state
        move.with_user(self.reviewer).action_mark_reviewed()
        move.with_user(self.reviewer).action_mark_reviewed()
        self.assertEqual(move.review_state, "reviewed")
        move.with_user(self.reviewer).button_draft()
        self.assertEqual(move.state, "draft")
        self.assertEqual(move.review_state, "not_reviewed")

        # Draft moves cannot be reviewed or reset via wizard
        with self.assertRaises(UserError):
            move.with_user(self.reviewer).action_mark_reviewed()
        with self.assertRaises(UserError):
            move.with_user(self.reviewer).action_open_reset_draft_wizard()
        draft_wizard = (
            self.env["account.move.review.wizard"]
            .with_user(self.reviewer)
            .create({"move_id": move.id})
        )
        with self.assertRaises(UserError):
            draft_wizard.action_confirm_reset_to_draft()

        # Non-reviewer cannot confirm wizard even if invoked directly
        move.with_user(self.accountant).action_post()
        direct_wizard = self.env["account.move.review.wizard"].create(
            {"move_id": move.id}
        )
        with self.assertRaises(AccessError):
            direct_wizard.with_user(self.accountant).action_confirm_reset_to_draft()

        # Move created by system root has no default notification recipient
        root_move = self._create_posted_move(self.env.ref("base.user_root"))
        self.assertFalse(root_move._default_review_recipient())

    def test_payment_draft_guard_and_review_workflow(self):
        self.company.restrict_move_draft_to_reviewers = True
        bank_journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "in", ("bank", "cash"))],
            limit=1,
        )
        inbound_line = bank_journal.inbound_payment_method_line_ids[:1]
        if inbound_line and not inbound_line.payment_account_id:
            inbound_line.payment_account_id = self.accounts[0]
        partner = self.env["res.partner"].create({"name": "Review Test Partner"})
        payment = (
            self.env["account.payment"]
            .with_user(self.accountant)
            .create(
                {
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": partner.id,
                    "amount": 50.0,
                    "journal_id": bank_journal.id,
                    "payment_method_line_id": inbound_line.id,
                }
            )
        )
        self.assertFalse(payment.review_move_posted)
        payment.with_user(self.accountant).action_post()

        with self.assertRaises(AccessError):
            payment.with_user(self.accountant).action_draft()
        with self.assertRaises(AccessError):
            payment.with_user(self.accountant).action_mark_move_reviewed()
        with self.assertRaises(AccessError):
            payment.with_user(self.accountant).action_open_reset_draft_wizard()

        # Reviewer can mark payment move reviewed and reset it via wizard
        payment.with_user(self.reviewer).action_mark_move_reviewed()
        self.assertTrue(payment.review_move_posted)
        self.assertEqual(payment.move_review_state, "reviewed")
        action = payment.with_user(self.reviewer).action_open_reset_draft_wizard()
        self.assertEqual(action["res_model"], "account.move.review.wizard")
        wizard = (
            self.env["account.move.review.wizard"]
            .with_user(self.reviewer)
            .with_context(**action["context"])
            .create({"notes": "", "recipient_user_id": False})
        )
        wizard.action_confirm_reset_to_draft()
        self.assertEqual(payment.state, "draft")
        self.assertEqual(payment.move_review_state, "returned")

        # Calling wizard helper on a cancelled payment delegates to action_draft
        payment.with_user(self.reviewer).action_cancel()
        payment.with_user(self.reviewer).action_open_reset_draft_wizard()
        self.assertEqual(payment.state, "draft")
