# Copyright 2024 Foodles (https://www.foodles.co/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.osv import expression


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_older_conflicting_invoices_domain(self):
        self.ensure_one()
        if not self.invoice_date or not self.journal_id.sequence_id.use_date_range:
            return super()._get_older_conflicting_invoices_domain()
        date_range = self.journal_id.sequence_id._get_current_sequence(self.date)
        return expression.AND(
            [
                self._get_conflicting_invoices_domain(),
                [
                    ("state", "=", "draft"),
                    ("invoice_date", "!=", False),
                    ("invoice_date", ">=", date_range.date_from),
                    ("invoice_date", "<", self.invoice_date),
                ],
            ]
        )

    def _get_newer_conflicting_invoices_domain(self):
        self.ensure_one()
        if not self.invoice_date or not self.journal_id.sequence_id.use_date_range:
            return super()._get_newer_conflicting_invoices_domain()
        date_range = self.journal_id.sequence_id._get_current_sequence(self.date)
        return expression.AND(
            [
                self._get_conflicting_invoices_domain(),
                [
                    ("state", "=", "posted"),
                    ("invoice_date", ">", self.invoice_date),
                    ("invoice_date", "<=", date_range.date_to),
                ],
            ]
        )
