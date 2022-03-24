# Copyright 2022 ForgeFlow
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def handle_account_invoice_move_migration(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move_line aml
        SET asset_profile_id = COALESCE(ail.asset_profile_id, aml.asset_profile_id),
            asset_id = COALESCE(ail.asset_id, aml.asset_id)
        FROM account_invoice_line ail
        WHERE aml.old_invoice_line_id = ail.id AND
            (ail.asset_profile_id IS NOT NULL OR ail.asset_id IS NOT NULL)""",
    )


@openupgrade.migrate()
def migrate(env, version):
    handle_account_invoice_move_migration(env)
