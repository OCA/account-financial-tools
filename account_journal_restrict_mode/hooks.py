# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def post_init_hook(env):
    """Enable restrict mode on all journals"""
    journals_to_update = env["account.journal"].search(
        [("restrict_mode_hash_table", "=", False)]
    )
    journals_to_update.write({"restrict_mode_hash_table": True})
