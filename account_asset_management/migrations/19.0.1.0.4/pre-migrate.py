from openupgradelib import openupgrade


def migrate(cr, version):
    # Already company dependent when coming from 18.0.1.1.4 or later
    cr.execute(
        """
        SELECT data_type FROM information_schema.columns
        WHERE table_name = 'account_account' AND column_name = 'asset_profile_id'
        """
    )
    row = cr.fetchone()
    if not row or row[0] in ("json", "jsonb"):
        return
    openupgrade.logged_query(
        cr,
        """
        ALTER TABLE account_account
        RENAME COLUMN asset_profile_id TO asset_profile_id_old;
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        ALTER TABLE account_account ADD COLUMN asset_profile_id json;
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE account_account
        SET asset_profile_id = old_value_id.value
        FROM (
            SELECT id, JSON_OBJECT_AGG (company_id, id) AS "value"
            FROM account_asset_profile group by id
        ) old_value_id
        WHERE account_account.asset_profile_id_old = old_value_id.id;
        """,
    )
