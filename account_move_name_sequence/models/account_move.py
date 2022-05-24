# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    name = fields.Char(compute="_compute_name_by_sequence")
    # highest_name, sequence_prefix and sequence_number are not needed any more
    # -> compute=False to improve perf
    highest_name = fields.Char(compute=False)
    sequence_prefix = fields.Char(compute=False)
    sequence_number = fields.Integer(compute=False)

    _sql_constraints = [
        (
            "name_state_diagonal",
            "CHECK(COALESCE(name, '') NOT IN ('/', '') OR state!='posted')",
            'A move can not be posted with name "/" or empty value\n'
            "Check the journal sequence, please",
        ),
    ]

    @api.depends("state", "journal_id", "date")
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
                and move.journal_id.sequence_id
            ):
                if (
                    move.move_type in ("out_refund", "in_refund")
                    and move.journal_id.type in ("sale", "purchase")
                    and move.journal_id.refund_sequence
                    and move.journal_id.refund_sequence_id
                ):
                    seq = move.journal_id.refund_sequence_id
                else:
                    seq = move.journal_id.sequence_id
                name = seq.next_by_id(sequence_date=move.date)
            move.name = name

    # We must by-pass this constraint of sequence.mixin
    def _constrains_date_sequence(self):
        return True
