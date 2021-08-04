# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """
    Column `purchase_id` of table `account_move_line` has been renamed to `purchase_order_id`
    because `purchase_order_id` is now in the core.
    """
    old_purchase_column = "purchase_id"
    new_purchase_column = "purchase_order_id"

    if not openupgrade.column_exists(env.cr, "account_move_line", new_purchase_column):
        openupgrade.rename_fields(
            env,
            [
                (
                    "account.move.line",
                    "account_move_line",
                    old_purchase_column,
                    new_purchase_column,
                ),
            ],
        )
