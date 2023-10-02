# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Enable restrict mode on all journals"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    journals_to_update = env["account.journal"].search(
        [("restrict_mode_hash_table", "=", False)]
    )
    journals_to_update.write({"restrict_mode_hash_table": True})
