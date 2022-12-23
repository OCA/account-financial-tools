# Copyright 2022 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

ADDON = "account_journal_general_sequence"


class AccountMove(models.Model):
    _inherit = "account.move"

    _sql_constraints = [
        (
            "entry_number_unique",
            "UNIQUE(entry_number, company_id)",
            "Entry number must be unique per company.",
        ),
    ]

    entry_number = fields.Char(
        index=True,
        readonly=True,
        tracking=True,
        store=True,
        compute="_compute_entry_number",
        help="Automatic numbering, based on journal configuration.",
    )

    @api.depends("state")
    def _compute_entry_number(self):
        """Assign an entry number when posting."""
        # Skip if installing module, for performance reasons
        if self.env.context.get("module") == ADDON:
            module = self.env["ir.module.module"].search([("name", "=", ADDON)])
            if module.state == "to install":
                _logger.info(
                    "Skipping entry number generation at install for %s.",
                    self,
                )
                return
        canceled = self.filtered_domain(
            [("state", "=", "cancel"), ("entry_number", "!=", False)]
        )
        canceled.entry_number = False
        if canceled:
            no_gap_seqs = canceled.mapped(
                "journal_id.entry_number_sequence_id"
            ).filtered_domain([("implementation", "=", "no_gap")])
            if no_gap_seqs:
                _logger.warning(
                    "Emptied entry_number for %r after cancellation. "
                    "This created gaps on %r.",
                    canceled,
                    no_gap_seqs,
                )
        chosen = self.filtered_domain(
            [("state", "=", "posted"), ("entry_number", "=", False)]
        )
        for move in chosen.sorted(lambda one: (one.date, one.name, one.id)):
            move.entry_number = move.journal_id.entry_number_sequence_id._next(
                move.date
            )
        if chosen:
            _logger.info("Added entry_number to %r", chosen)
