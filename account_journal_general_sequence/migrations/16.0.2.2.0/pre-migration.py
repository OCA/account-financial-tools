# Copyright 2026 Pol Reig
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Switch entry number sequences from no_gap to standard.

    no_gap uses FOR UPDATE NOWAIT which conflicts with the savepoint retry
    loop in account_sequence._set_next_sequence(), causing LockNotAvailable
    errors when importing bank statements with multiple lines.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    seqs = env["ir.sequence"].search([
        ("code", "=", "account_journal_general_sequence.default"),
        ("implementation", "=", "no_gap"),
    ])
    for seq in seqs:
        seq.write({"implementation": "standard"})
        # After switching to standard, Odoo creates the PostgreSQL sequence
        # starting from 1. We need to restore the correct next value for each
        # date range, otherwise already-used numbers would be reassigned.
        for date_range in seq.date_range_ids:
            date_range.number_next_actual = date_range.number_next
