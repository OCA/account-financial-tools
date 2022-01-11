# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import Form, SavepointCase


class TestInvoiceReversal(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestInvoiceReversal, cls).setUpClass()
        cls.account_type_receivable = cls.env["account.account.type"].create(
            {"name": "Test Receivable", "type": "receivable", "internal_group": "asset"}
        )
        cls.account_type_regular = cls.env["account.account.type"].create(
            {"name": "Test Regular", "type": "other", "internal_group": "income"}
        )
        cls.account_receivable = cls.env["account.account"].create(
            {
                "name": "Test Receivable",
                "code": "TEST_AR",
                "user_type_id": cls.account_type_receivable.id,
                "reconcile": True,
            }
        )
        cls.account_income = cls.env["account.account"].create(
            {
                "name": "Test Income",
                "code": "TEST_IN",
                "user_type_id": cls.account_type_regular.id,
                "reconcile": False,
            }
        )
        cls.sale_journal = cls.env["account.journal"].search([("type", "=", "sale")])[0]
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test",
                "property_account_receivable_id": cls.account_receivable.id,
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "name": "Test Customer Invoice",
                "journal_id": cls.sale_journal.id,
                "partner_id": cls.partner.id,
                "type": "out_invoice",
            }
        )
        cls.invoice_line = {
            "move_id": cls.invoice.id,
            "name": "Line 1",
            "price_unit": 200.0,
            "account_id": cls.account_income.id,
            "quantity": 1,
        }
        cls.invoice.write({"invoice_line_ids": [(0, 0, cls.invoice_line)]})

    def test_journal_invoice_cancel_reversal(self):
        """ Tests cancel with reversal, end result must follow,
        - Reversal journal entry is created, and reconciled with original entry
        - Status is changed to cancel
        """
        # Test journal
        self.sale_journal.write({"cancel_method": "normal"})
        self.sale_journal.invalidate_cache()
        self.sale_journal.write(
            {"cancel_method": "reversal", "use_different_journal": True}
        )
        # Open invoice
        self.invoice.post()
        # Normal cancel button is not usable.
        with self.assertRaises(Exception):
            self.invoice.button_cancel()
        # Click Cancel will open reverse document wizard
        res = self.invoice.button_cancel_reversal()
        self.assertEqual(res["res_model"], "reverse.account.document")
        # Cancel invoice
        ctx = {"active_model": "account.move", "active_ids": [self.invoice.id]}
        f = Form(self.env[res["res_model"]].with_context(ctx))
        cancel_wizard = f.save()
        cancel_wizard.action_cancel()
        reversed_move = self.invoice.reverse_entry_id
        move_reconcile = self.invoice.mapped("line_ids").mapped("full_reconcile_id")
        reversed_move_reconcile = reversed_move.mapped("line_ids").mapped(
            "full_reconcile_id"
        )
        # Check
        self.assertTrue(move_reconcile)
        self.assertTrue(reversed_move_reconcile)
        self.assertEqual(move_reconcile, reversed_move_reconcile)
        self.assertEqual(self.invoice.state, "posted")
        self.assertEqual(self.invoice.cancel_reversal, True)
        # After reversed, set to draft is not allowed
        with self.assertRaises(Exception):
            self.invoice.button_draft()
