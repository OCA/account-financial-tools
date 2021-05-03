# Copyright 2020 ForgeFlow <http://www.forgeflow.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_field_renames = [
    ("account.move.line", "account_move_line", "sale_id", "sale_order_id",),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
