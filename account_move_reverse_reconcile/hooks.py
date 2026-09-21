# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from openupgradelib import openupgrade


def pre_init_hook(env):
    if openupgrade.column_exists(env.cr, "account_move", "reversal_post_automatic_reconcile"):
        return

    field_spec = [
        (
            "reversal_post_automatic_reconcile",
            "account.move",
            "account_move",
            "selection",
            "varchar",
            "account_move_reverse_reconcile",
            "reconcile",
        )
    ]
    openupgrade.add_fields(env, field_spec=field_spec)
