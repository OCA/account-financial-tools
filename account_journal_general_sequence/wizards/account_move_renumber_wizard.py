# Copyright 2022 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from datetime import date

from odoo import _, api, exceptions, fields, models


class AccountMoveRenumberWizard(models.TransientModel):
    _name = "account.move.renumber.wizard"
    _description = "Account move entry renumbering wizard"

    starting_date = fields.Date(
        required=True,
        default=lambda self: self._default_starting_date(),
        help="Renumber account moves starting this day.",
    )
    starting_number = fields.Integer(
        default=1, help="Reset sequence to this number before starting."
    )
    available_sequence_ids = fields.Many2many(
        comodel_name="ir.sequence",
        string="Available sequences",
        default=lambda self: self._default_available_sequence_ids(),
    )
    sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Sequence",
        required=True,
        default=lambda self: self._default_entry_number_sequence(),
        domain="[('id', 'in', available_sequence_ids)]",
        help="Sequence to use for renumbering. Affects all journals that use this sequence.",
    )

    @api.model
    def _default_starting_date(self):
        """Start by default on day 1 of current year."""
        return date(date.today().year, 1, 1)

    @api.model
    def _default_entry_number_sequence(self):
        """Get default sequence if it exists."""
        return self.env["ir.sequence"].search(
            [
                "&",
                ("code", "=", "account_journal_general_sequence.default"),
                ("company_id", "in", self.env.companies.ids),
            ]
        )

    @api.model
    def _default_available_sequence_ids(self):
        """Let view display only journal-related sequences."""
        return (
            self.env["account.journal"]
            .search([("company_id", "in", self.env.companies.ids)])
            .mapped("entry_number_sequence_id")
        )

    def action_renumber(self):
        """Renumber moves.

        Makes sure moves exist. Sorts them. Resets sequences. Renumbers them.
        """
        # Find posted moves that match wizard criteria
        moves = self.env["account.move"].search(
            [
                ("state", "=", "posted"),
                ("date", ">=", self.starting_date),
                ("journal_id.entry_number_sequence_id", "=", self.sequence_id.id),
            ],
            order="date, id",
        )
        if not moves:
            raise exceptions.UserError(_("No account moves found."))
        # Reset sequence
        future_ranges = self.env["ir.sequence.date_range"].search(
            [
                ("date_from", ">", self.starting_date),
                ("sequence_id", "=", self.sequence_id.id),
            ]
        )
        # Safe `sudo` calls; wizard only available for accounting managers
        future_ranges.sudo().unlink()
        current_range = self.sequence_id._get_current_sequence(self.starting_date)
        current_range.sudo().number_next = self.starting_number
        self.sequence_id.sudo().number_next = self.starting_number
        # Renumber the moves
        moves = moves.with_context(skip_invoice_sync=True)
        moves.entry_number = False
        moves.flush_recordset(["entry_number"])
        moves._compute_entry_number()
