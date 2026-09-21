# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMoveFromEPDGenerator(models.Model):
    _name = "account.move.from_epd.generator"
    _description = "Generate account move from early payment discount"

    origin_move_id = fields.Many2one("account.move", readonly=True)
    epd_move_journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        required=True,
        domain=[("type", "=", "general")],
    )
    epd_move_date = fields.Date(string="Date", required=True, default=fields.Date.today)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if (
            "origin_move_id" in fields_list
            and self.env.context.get("active_model") == "account.move"
            and self.env.context.get("active_id")
        ):
            res["origin_move_id"] = self.env.context["active_id"]
        return res

    def action_generate(self):
        """Create and post a journal entry materialising the Early Payment
        Discount (EPD) on *origin_move_id*, then reconcile the resulting
        receivable/payable line against the invoice.

        This produces the same accounting effect as registering a full payment
        with the discount applied, without actually recording a payment.

        For invoices with taxes and ``early_pay_discount_computation = 'included'``
        the generated entry contains separate base and tax write-off lines so
        that the tax report is updated correctly.  For all other cases a single
        discount line is created.

        Returns an ``ir.actions.act_window`` action pointing to the new move.
        """
        self.ensure_one()
        invoice = self.origin_move_id

        payment_term = invoice.invoice_payment_term_id
        if not payment_term.early_discount:
            raise UserError(
                self.env._(
                    "The payment term of %(invoice)s does not have an early "
                    "payment discount configured.",
                    invoice=invoice.name,
                )
            )

        payment_term_line = invoice.line_ids.filtered(
            lambda li: li.display_type == "payment_term"
        )
        if not payment_term_line:
            raise UserError(
                self.env._(
                    "No payment-term line found on invoice %(invoice)s.",
                    invoice=invoice.name,
                )
            )
        payment_term_line.ensure_one()

        partner = invoice.partner_id
        rec_pay_account = payment_term_line.account_id
        currency = invoice.currency_id

        # Stored full EPD amounts (company currency / invoice currency).
        # These are independent of any prior partial reconciliation.
        term_balance = payment_term_line.balance - payment_term_line.discount_balance
        term_amount_currency = (
            payment_term_line.amount_currency
            - payment_term_line.discount_amount_currency
        )

        # Use Odoo's internal helper to build the EPD write-off lines.
        # - For 'included' computation with taxes it returns base_lines and
        #   tax_lines (with a rounding fix that guarantees their sum equals
        #   term_balance).
        # - For all other cases it returns a single term_line carrying the
        #   full discount amount.
        epd_values = invoice._get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line()  # noqa

        epd_line_vals_list = []
        for category in ("term_lines", "base_lines", "tax_lines"):
            for grouping_dict, vals in (
                epd_values[category].get(payment_term_line, {}).items()
            ):
                epd_line_vals_list.append(
                    {**dict(grouping_dict), **vals, "partner_id": partner.id}
                )

        if not epd_line_vals_list:
            raise UserError(
                self.env._(
                    "Could not compute EPD lines for invoice %(invoice)s.",
                    invoice=invoice.name,
                )
            )

        # The counter receivable/payable line always uses the stored full EPD
        # amounts so the entry balances regardless of prior reconciliations.
        counter_line_vals = {
            "name": invoice.name,
            "account_id": rec_pay_account.id,
            "partner_id": partner.id,
            "currency_id": currency.id,
            "amount_currency": -term_amount_currency,
            "balance": -term_balance,
        }

        epd_move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.epd_move_journal_id.id,
                "date": self.epd_move_date,
                "ref": self.env._("EPD - %(invoice)s", invoice=invoice.name),
                "partner_id": partner.id,
                "line_ids": (
                    [(0, 0, v) for v in epd_line_vals_list]
                    + [(0, 0, counter_line_vals)]
                ),
            }
        )
        epd_move.action_post()

        invoice.generated_epd_move_id = epd_move

        epd_receivable_line = epd_move.line_ids.filtered(
            lambda li: li.account_id == rec_pay_account
        )
        invoice_open_lines = invoice.line_ids.filtered(
            lambda li: li.account_id == rec_pay_account and not li.reconciled
        )
        (epd_receivable_line | invoice_open_lines).reconcile()

        invoice.message_post(
            body=Markup(
                self.env._("Early payment discount was materialized in %(link)s")
            )
            % {"link": epd_move._get_html_link()}
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": epd_move.id,
            "view_mode": "form",
        }
