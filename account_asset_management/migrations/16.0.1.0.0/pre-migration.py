# Copyright 2024 Moduon Team S.L. <info@moduon.team>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Migrate Analytic Accounts to Analytic Distributions on Assets and Profiles"""
    openupgrade.add_fields(
        env,
        [
            (
                "analytic_distribution",
                "account.asset",
                "account_asset",
                "json",
                "jsonb",
                "account_asset_management",
                None,
            ),
            (
                "analytic_distribution",
                "account.asset.profile",
                "account_asset_profile",
                "json",
                "jsonb",
                "account_asset_management",
                None,
            ),
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
            UPDATE account_asset
            SET analytic_distribution = jsonb_build_object(
                account_analytic_id::text, 100.0
            )
            WHERE account_analytic_id IS NOT NULL
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_asset_profile
        SET analytic_distribution = jsonb_build_object(
            account_analytic_id::text, 100.0
        )
        WHERE account_analytic_id IS NOT NULL
        """,
    )
