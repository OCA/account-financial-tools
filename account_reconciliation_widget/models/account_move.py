from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def _create_writeoff(self, writeoff_vals):
        """Create a writeoff move per journal for the account.move.lines in
         self. If debit/credit is not specified in vals, the writeoff amount
         will be computed as the sum of amount_residual of the given recordset.

        :param writeoff_vals: list of dicts containing values suitable for
            account_move_line.create(). The data in vals will be processed to
            create bot writeoff account.move.line and their enclosing
            account.move.
        """

        def compute_writeoff_counterpart_vals(values):
            line_values = values.copy()
            line_values["debit"], line_values["credit"] = (
                line_values["credit"],
                line_values["debit"],
            )
            if "amount_currency" in values:
                line_values["amount_currency"] = -line_values["amount_currency"]
            return line_values

        # Group writeoff_vals by journals
        writeoff_dict = {}
        for val in writeoff_vals:
            journal_id = val.get("journal_id", False)
            if not writeoff_dict.get(journal_id, False):
                writeoff_dict[journal_id] = [val]
            else:
                writeoff_dict[journal_id].append(val)

        partner_id = (
            self.env["res.partner"]._find_accounting_partner(self[0].partner_id).id
        )
        company_currency = self[0].account_id.company_id.currency_id
        writeoff_currency = self[0].account_id.currency_id or company_currency
        line_to_reconcile = self.env["account.move.line"]
        # Iterate and create one writeoff by journal
        writeoff_moves = self.env["account.move"]
        for journal_id, lines in writeoff_dict.items():
            total = 0
            total_currency = 0
            writeoff_lines = []
            date = fields.Date.today()
            for vals in lines:
                # Check and complete vals
                if "account_id" not in vals or "journal_id" not in vals:
                    raise UserError(
                        _(
                            "It is mandatory to specify an account and a "
                            "journal to create a write-off."
                        )
                    )
                if ("debit" in vals) ^ ("credit" in vals):
                    raise UserError(_("Either pass both debit and credit or none."))
                if "date" not in vals:
                    vals["date"] = self._context.get("date_p") or fields.Date.today()
                vals["date"] = fields.Date.to_date(vals["date"])
                if vals["date"] and vals["date"] < date:
                    date = vals["date"]
                if "name" not in vals:
                    vals["name"] = self._context.get("comment") or _("Write-Off")
                if "analytic_account_id" not in vals:
                    vals["analytic_account_id"] = self.env.context.get(
                        "analytic_id", False
                    )
                # compute the writeoff amount if not given
                if "credit" not in vals and "debit" not in vals:
                    amount = sum([r.amount_residual for r in self])
                    vals["credit"] = amount > 0 and amount or 0.0
                    vals["debit"] = amount < 0 and abs(amount) or 0.0
                vals["partner_id"] = partner_id
                total += vals["debit"] - vals["credit"]
                if (
                    "amount_currency" not in vals
                    and writeoff_currency != company_currency
                ):
                    vals["currency_id"] = writeoff_currency.id
                    sign = 1 if vals["debit"] > 0 else -1
                    vals["amount_currency"] = sign * abs(
                        sum([r.amount_residual_currency for r in self])
                    )
                    total_currency += vals["amount_currency"]

                writeoff_lines.append(compute_writeoff_counterpart_vals(vals))

            # Create balance line
            writeoff_lines.append(
                {
                    "name": _("Write-Off"),
                    "debit": total > 0 and total or 0.0,
                    "credit": total < 0 and -total or 0.0,
                    "amount_currency": total_currency,
                    "currency_id": total_currency and writeoff_currency.id or False,
                    "journal_id": journal_id,
                    "account_id": self[0].account_id.id,
                    "partner_id": partner_id,
                }
            )

            # Create the move
            writeoff_move = self.env["account.move"].create(
                {
                    "journal_id": journal_id,
                    "date": date,
                    "state": "draft",
                    "line_ids": [(0, 0, line) for line in writeoff_lines],
                }
            )
            writeoff_moves += writeoff_move
            line_to_reconcile += writeoff_move.line_ids.filtered(
                lambda r: r.account_id == self[0].account_id
            ).sorted(key="id")[-1:]

        # post all the writeoff moves at once
        if writeoff_moves:
            writeoff_moves.action_post()

        # Return the writeoff move.line which is to be reconciled
        return line_to_reconcile
