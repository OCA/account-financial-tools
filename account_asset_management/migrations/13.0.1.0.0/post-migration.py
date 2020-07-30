# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade  # pylint: disable=W7936

@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(
        env.cr, "account_asset_management", "migrations/13.0.1.0.0/noupdate_changes.xml"
    )