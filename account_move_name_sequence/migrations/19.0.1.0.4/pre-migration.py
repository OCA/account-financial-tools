# Copyright 2025 Le Filament (https://www.le-filament.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    """
    made_sequence_gap relies on sequence_number / sequence_prefix, which this
    module only sets on hashed journals. Migration scripts initialize this value
    to True and then recompute it based on those fields, so force all
    made_sequence_gap to False when these fields are not set.
    """
    cr.execute(
        """
        UPDATE account_move am
        SET made_sequence_gap = False
        FROM account_journal aj
        WHERE am.journal_id = aj.id
            AND aj.restrict_mode_hash_table IS NOT TRUE
            AND am.made_sequence_gap IS TRUE
        """
    )
