# Copyright 2015-2019 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2021 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import format_date


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_conflicting_invoices_domain(self):
        self.ensure_one()
        domain = [
            ("journal_id", "=", self.journal_id.id),
            ("move_type", "!=", "entry"),
        ]
        if self.journal_id.refund_sequence:
            domain.append(("move_type", "=", self.move_type))
        return domain

    def _get_older_conflicting_invoices_domain(self):
        self.ensure_one()
        return expression.AND(
            [
                self._get_conflicting_invoices_domain(),
                [
                    ("state", "=", "draft"),
                    ("invoice_date", "!=", False),
                    ("invoice_date", "<", self.invoice_date),
                ],
            ]
        )

    def _raise_older_conflicting_invoices(self):
        self.ensure_one()
        raise UserError(
            _(
                "Chronology conflict: A conflicting draft invoice dated before "
                "{date_invoice} exists, please validate it first."
            ).format(date_invoice=format_date(self.env, self.invoice_date))
        )

    def _get_newer_conflicting_invoices_domain(self):
        self.ensure_one()
        return expression.AND(
            [
                self._get_conflicting_invoices_domain(),
                [("state", "=", "posted"), ("invoice_date", ">", self.invoice_date)],
            ]
        )

    def _raise_newer_conflicting_invoices(self):
        self.ensure_one()
        raise UserError(
            _(
                "Chronology conflict: A conflicting validated invoice dated after "
                "{date_invoice} exists."
            ).format(date_invoice=format_date(self.env, self.invoice_date))
        )

    def _get_sequence_order_conflicting_invoices_domain(self):
        self.ensure_one()

        if not self.name or self.name == "/":
            return expression.FALSE_DOMAIN

        last_sequence = self._get_last_sequence()
        if not last_sequence or self.name > last_sequence:
            return expression.FALSE_DOMAIN

        return expression.AND(
            [
                [("name", "=", last_sequence)],
                self._get_conflicting_invoices_domain(),
                [("state", "=", "posted"), ("invoice_date", "<", self.invoice_date)],
            ]
        )

    def _raise_sequence_ordering_conflict(self):
        self.ensure_one()
        raise UserError(
            _(
                "Chronology conflict: An invoice with a higher number {highest_name}"
                " dated before {date_invoice} exists."
            ).format(
                highest_name=self._get_last_sequence(),
                date_invoice=format_date(self.env, self.invoice_date),
            )
        )

    def write(self, vals):
        if vals.get("state") != "posted":
            return super().write(vals)
        previously_validated = self.filtered(lambda m: m.name and m.name != "/")
        newly_posted = self.filtered(lambda move: move.state != "posted")
        res = super().write(vals)
        for move in newly_posted & self.filtered("journal_id.check_chronology"):
            if self.search(
                move._get_sequence_order_conflicting_invoices_domain(), limit=1
            ):
                move._raise_sequence_ordering_conflict()
            if self.search(move._get_older_conflicting_invoices_domain(), limit=1):
                move._raise_older_conflicting_invoices()
            if move in previously_validated:
                continue
            if self.search(move._get_newer_conflicting_invoices_domain(), limit=1):
                move._raise_newer_conflicting_invoices()

        return res
