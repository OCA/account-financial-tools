# Copyright 2025 Akretion (https://www.akretion.com) — original 18.0 fix in PR #2160
# Copyright 2026 Ledo Enterprises — 19.0 forward-port + idempotency check
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Convert ``account_account.asset_profile_id`` from a plain Many2one (int FK)
to a ``company_dependent`` field (jsonb per-company storage).

Required for Odoo 18+ where ``account.account`` is shared across companies — the
old single-FK column cannot express per-company asset profile choices and raises
multicompany access errors when accounts cross company boundaries.

Forward-port of https://github.com/OCA/account-financial-tools/pull/2160 (Benoît
Guillot, Akretion). Idempotent: if the column is already jsonb (because the user
upgraded from a patched 18.0 that already had #2160 merged), the migration is a
no-op.
"""

from openupgradelib import openupgrade


def migrate(cr, version):
    # Idempotency: a patched-18.0 install already has the column as jsonb.
    # Inspect information_schema and skip the conversion in that case.
    cr.execute(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'account_account'
          AND column_name = 'asset_profile_id'
        """
    )
    row = cr.fetchone()
    if row and row[0] in ("jsonb", "json"):
        # Already converted — no-op.
        return
    # Standard path: int FK column on a freshly-upgraded 18.0 (pre-#2160) install.
    # Preserve existing data by renaming to *_old, create the new jsonb column,
    # and rebuild a per-company dict from the profile's own company_id.
    openupgrade.logged_query(
        cr,
        """
        ALTER TABLE account_account
        RENAME COLUMN asset_profile_id TO asset_profile_id_old
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        ALTER TABLE account_account ADD COLUMN asset_profile_id jsonb
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE account_account
        SET asset_profile_id = old_value_id.value
        FROM (
            SELECT id, JSON_OBJECT_AGG(company_id, id) AS "value"
            FROM account_asset_profile
            GROUP BY id
        ) old_value_id
        WHERE account_account.asset_profile_id_old = old_value_id.id
        """,
    )
