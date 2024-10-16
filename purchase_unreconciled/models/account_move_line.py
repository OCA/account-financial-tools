# Copyright 2019-21 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import _, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_writeoff_amounts(self):
        precision = self.env["decimal.precision"].precision_get("Account")
        writeoff_amount = round(
            sum(line["amount_residual"] for line in self), precision
        )
        writeoff_amount_curr = round(
            sum(line["amount_residual_currency"] for line in self), precision
        )
        if writeoff_amount_curr and not writeoff_amount:
            # Data inconsistency, do not create the write-off
            return (0.0, 0.0, True)
        first_currency = self[0]["currency_id"]
        if all([line["currency_id"] == first_currency for line in self]):
            same_curr = True
        else:
            same_curr = False

        return (
            writeoff_amount,
            writeoff_amount_curr,
            same_curr,
        )

    def _create_writeoff(self, writeoff_vals):
        (
            amount_writeoff,
            amount_writeoff_curr,
            same_curr,
        ) = self._get_writeoff_amounts()
        if not amount_writeoff:
            return self.env["account.move.line"]
        partners = self.mapped("partner_id")
        move_date = writeoff_vals.get("date", datetime.now())
        write_off_vals = {
            "name": _("Automatic writeoff"),
            "amount_currency": same_curr and amount_writeoff_curr or amount_writeoff,
            "debit": amount_writeoff > 0.0 and amount_writeoff or 0.0,
            "credit": amount_writeoff < 0.0 and -amount_writeoff or 0.0,
            "partner_id": len(partners) == 1 and partners.id or False,
            "account_id": writeoff_vals["account_id"],
            "date": move_date,
            "journal_id": writeoff_vals["journal_id"],
            "currency_id": writeoff_vals.get("currency_id", False),
            "product_id": writeoff_vals["product_id"],
            "purchase_order_id": writeoff_vals["purchase_order_id"],
            "purchase_line_id": writeoff_vals["purchase_line_id"],
        }
        counterpart_account = self.mapped("account_id")
        if len(counterpart_account) != 1:
            raise ValidationError(_("Cannot write-off more than one account"))
        counter_part = write_off_vals.copy()
        counter_part["debit"] = write_off_vals["credit"]
        counter_part["credit"] = write_off_vals["debit"]
        counter_part["amount_currency"] = -write_off_vals["amount_currency"]
        counter_part["account_id"] = (counterpart_account.id,)

        move = self.env["account.move"].create(
            {
                "date": move_date,
                "journal_id": writeoff_vals["journal_id"],
                "currency_id": writeoff_vals.get("currency_id", False),
                "line_ids": [(0, 0, write_off_vals), (0, 0, counter_part)],
            }
        )
        if writeoff_vals.get("purchase_order_id", False):
            # done this way because purchase_order_id is a related field and will
            # not being assign on create. Cannot assign purchase_line_id because
            # it is a generic write-off for the whole PO
            self.env.cr.execute(
                """UPDATE account_move_line SET purchase_order_id = %s
            WHERE id in %s
            """,
                (writeoff_vals["purchase_order_id"], tuple(move.line_ids.ids)),
            )
        move.action_post()
        return move.line_ids.filtered(
            lambda line: line.account_id.id == counterpart_account.id
        )
