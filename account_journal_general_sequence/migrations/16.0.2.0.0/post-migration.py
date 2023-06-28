# Copyright 2023 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)
from odoo import SUPERUSER_ID, api, fields


def migrate(cr, version):
    """One journal sequence per company."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    journals = env["account.journal"].search(
        [
            (
                "entry_number_sequence_id.code",
                "=",
                "account_journal_general_sequence.default",
            )
        ]
    )
    for journal in journals:
        if journal.company_id != journal.entry_number_sequence_id.company_id:
            new_sequence = env["ir.sequence"].search(
                [
                    ("code", "=", "account_journal_general_sequence.default"),
                    ("company_id", "=", journal.company_id.id),
                ]
            ) or journal.entry_number_sequence_id.copy(
                {
                    "company_id": journal.company_id.id,
                    "name": "{} ({})".format(
                        journal.entry_number_sequence_id.name, journal.company_id.name
                    ),
                    "number_next_actual": journal.entry_number_sequence_id.number_next_actual,
                    "date_range_ids": [
                        fields.Command.create(
                            {
                                "date_from": rng.date_from,
                                "date_to": rng.date_to,
                                "number_next_actual": rng.number_next_actual,
                            }
                        )
                        for rng in journal.entry_number_sequence_id.date_range_ids
                    ],
                }
            )
            journal.entry_number_sequence_id = new_sequence
