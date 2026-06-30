# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    name = fields.Char(compute="_compute_name_by_sequence")
    # highest_name is not needed any more
    # -> compute=False to improve perf
    highest_name = fields.Char(compute=False)
    # made_sequence_hole is not relevant anymore (since based on sequence_prefix/number)
    # -> compute=False to improve perf and to avoid displaying warning
    made_sequence_hole = fields.Boolean(compute=False)

    _sql_constraints = [
        (
            "name_state_diagonal",
            "CHECK(COALESCE(name, '') NOT IN ('/', '') OR state!='posted')",
            'A move can not be posted with name "/" or empty value\n'
            "Check the journal sequence, please",
        ),
    ]

    def _get_sequence_for_move(self):
        self.ensure_one()
        if (
            self.move_type in ("out_refund", "in_refund")
            and self.journal_id.type in ("sale", "purchase")
            and self.journal_id.refund_sequence
            and self.journal_id.refund_sequence_id
        ):
            return self.journal_id.refund_sequence_id
        if (
            self.origin_payment_id
            and self.origin_payment_id.payment_method_line_id.sequence_id
        ):
            return self.origin_payment_id.payment_method_line_id.sequence_id
        return self.journal_id.sequence_id

    @api.depends("name")
    def _compute_split_sequence(self):
        """
        Replace original compute function from Odoo account module
        to compute sequend and prefix from name only if journal is
        in secured mode (restrict_mode_hash_table)
        Since both sequence_prefix and sequence_number are needed for
        computing hash since Odoo v18.0
        """
        moves = self.filtered(
            lambda move: move.name
            and move.name != "/"
            and move.journal_id
            and move.move_type
            and move.restrict_mode_hash_table
        )
        # Handle moves grouped by sequence and year
        for (sequence, year), grouped_moves in moves.grouped(
            lambda m: (m._get_sequence_for_move(), m.date.year)
        ).items():
            if not sequence:
                continue
            # Retrieve prefix and suffix to extract number
            prefix, suffix = sequence._get_prefix_suffix(
                date=f"{year}-01-01", date_range=f"{year}-01-01"
            )
            # Set prefix
            grouped_moves.sequence_prefix = prefix
            for move in grouped_moves:
                # Get number for each move
                move.sequence_number = int(
                    move.name[len(prefix) : len(move.name) - len(suffix)]
                )

    @api.depends(
        "state",
        "journal_id",
        "date",
        "origin_payment_id.payment_method_line_id.sequence_id",
    )
    def _compute_name_by_sequence(self):
        for move in self:
            name = move.name or "/"
            # I can't use posted_before in this IF because
            # posted_before is set to True in _post() at the same
            # time as state is set to "posted"
            if (
                move.state == "posted"
                and (not move.name or move.name == "/")
                and move.journal_id
            ):
                seq = move._get_sequence_for_move()
                if seq:
                    # next_by_id(date) only applies on ir.sequence.date_range selection
                    # => we use with_context(ir_sequence_date=date).next_by_id()
                    # which applies on ir.sequence.date_range selection AND prefix
                    name = seq.with_context(ir_sequence_date=move.date).next_by_id()
            move.name = name
        # Force compute of sequence_prefix and sequence_number
        self._compute_split_sequence()
        # Force compute of fields depending on name
        self._inverse_name()

    # We must by-pass this constraint of sequence.mixin
    def _constrains_date_sequence(self):
        return True

    def _is_end_of_seq_chain(self):
        invoices_no_gap_sequences = self.filtered(
            lambda inv: inv._get_sequence_for_move()
            and inv._get_sequence_for_move().implementation == "no_gap"
        )
        invoices_other_sequences = self - invoices_no_gap_sequences
        if not invoices_other_sequences and invoices_no_gap_sequences:
            return False
        return super(AccountMove, invoices_other_sequences)._is_end_of_seq_chain()

    def _fetch_duplicate_reference(self, matching_states=("draft", "posted")):
        moves = self.filtered(
            lambda m: m.is_sale_document() or m.is_purchase_document() and m.ref
        )
        if moves:
            self.flush_model(["name", "journal_id", "move_type", "state"])
        return super()._fetch_duplicate_reference(matching_states=matching_states)

    def _get_last_sequence(self, relaxed=False, with_prefix=None):
        return super()._get_last_sequence(relaxed, None)

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        if not self.quick_edit_mode:
            self.name = "/"
            self._compute_name_by_sequence()

    def _post(self, soft=True):
        self.flush_recordset()
        return super()._post(soft=soft)

    @api.depends()
    def _compute_name(self):
        """Overwrite account module method in order to
        avoid side effect if legacy code call it directly
        like when creating entry from email.
        """
        return self._compute_name_by_sequence()
