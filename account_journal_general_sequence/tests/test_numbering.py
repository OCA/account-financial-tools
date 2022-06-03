# Copyright 2022 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from freezegun import freeze_time

from odoo.tests.common import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import TestAccountReconciliationCommon


@freeze_time("2022-05-11", tick=True)
@tagged("post_install", "-at_install")
class RenumberCase(TestAccountReconciliationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_invoice_gets_entry_number(self):
        # Draft invoice without entry number
        invoice = self._create_invoice()
        self.assertFalse(invoice.entry_number)
        # Gets one once posted
        invoice.action_post()
        self.assertTrue(invoice.entry_number.startswith("2022/"))
        # Lost number when canceled
        with mute_logger(
            "odoo.addons.account_journal_general_sequence.models.account_move"
        ):
            invoice.button_cancel()
        self.assertFalse(invoice.entry_number)

    def test_renumber(self):
        # Post invoices in wrong order
        new_invoice = self._create_invoice(
            date_invoice="2022-05-10", auto_validate=True
        )
        old_invoice = self._create_invoice(
            date_invoice="2022-04-30", auto_validate=True
        )
        self.assertLess(new_invoice.entry_number, old_invoice.entry_number)
        # Fix entry number order with wizard; default values are OK
        wiz_f = Form(self.env["account.move.renumber.wizard"])
        self.assertEqual(len(wiz_f.available_sequence_ids), 1)
        wiz = wiz_f.save()
        wiz.action_renumber()
        self.assertGreater(new_invoice.entry_number, old_invoice.entry_number)
        # Add opening move
        opening_invoice = self._create_invoice(
            date_invoice="2022-01-01", auto_validate=True
        )
        self.assertGreater(opening_invoice.entry_number, new_invoice.entry_number)
        # Renumber again, starting from zero
        wiz_f = Form(self.env["account.move.renumber.wizard"])
        wiz_f.starting_number = 0
        wiz = wiz_f.save()
        wiz.action_renumber()
        self.assertEqual(opening_invoice.entry_number, "2022/0000000000")

    def test_install_no_entry_number(self):
        """No entry numbers assigned on module installation."""
        # Imitate installation environment
        self.env = self.env(
            context=dict(self.env.context, module="account_journal_general_sequence")
        )
        self.env["ir.module.module"].search(
            [("name", "=", "account_journal_general_sequence")]
        ).state = "to install"
        # Do some action that would make the move get an entry number
        invoice = self._create_invoice()
        self.assertFalse(invoice.entry_number)
        invoice.action_post()
        # Ensure there's no entry number
        self.assertFalse(invoice.entry_number)
