# Copyright 2025 Le Filament (https://www.le-filament.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    for journal in env["account.journal"].search(
        [("restrict_mode_hash_table", "=", True)]
    ):
        journal_moves = env["account.move"].search(
            [
                ("state", "=", "posted"),
                ("journal_id", "=", journal.id),
                "|",
                ("sequence_prefix", "=", False),
                "|",
                ("sequence_number", "=", False),
                ("sequence_number", "=", 0),
            ]
        )
        for (move_type, year), moves in journal_moves.grouped(
            lambda m: (m.move_type, m.date.year)
        ).items():
            if (
                move_type in ["in_refund", "out_refund"]
                and journal.refund_sequence
                and journal.refund_sequence_id
            ):
                sequence = journal.refund_sequence_id
            else:
                sequence = journal.sequence_id
            prefix, suffix = sequence._get_prefix_suffix(
                date=f"{year}-01-01", date_range=f"{year}-01-01"
            )
            pattern = re.compile(f"{prefix}[0-9]{{{sequence.padding}}}{suffix}")
            filtered_moves = moves.filtered(lambda move: pattern.match(move.name))  # noqa: B023
            filtered_moves.sequence_prefix = prefix
            for move in filtered_moves:
                move.sequence_number = int(
                    move.name[len(prefix) : len(move.name) - len(suffix)]
                )
            filtered_moves._compute_made_sequence_gap()
