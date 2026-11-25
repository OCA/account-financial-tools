# Copyright 2026 Imaro Tech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(
        env,
        "account_asset_management",
        "migrations/17.0.1.2.2/noupdate_changes.xml",
    )
