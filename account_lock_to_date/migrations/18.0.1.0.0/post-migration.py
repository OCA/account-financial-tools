# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


def handle_new_lock_to_dates(env):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_company
        SET sale_lock_to_date = period_lock_to_date,
            purchase_lock_to_date = period_lock_to_date
        WHERE period_lock_to_date IS NOT NULL""",
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_company
        SET hard_lock_to_date = fiscalyear_lock_to_date
        WHERE fiscalyear_lock_to_date IS NOT NULL""",
    )


@openupgrade.migrate()
def migrate(env, version):
    handle_new_lock_to_dates(env)
