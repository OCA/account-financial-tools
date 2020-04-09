# Copyright 2020 ForgeFlow (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    pos = (
        env["account.move.line"]
        .search([("purchase_id", "!=", False), ("move_id.type", "=", "entry")])
        .mapped("purchase_id")
    )
    pos._compute_invoice()
