# Copyright 2024 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Migration from 15.0 to 16.0.

    No structural schema changes are required. The models account.move.budget
    and account.move.budget.line remain identical between versions.

    Key changes in Odoo 16.0 that are relevant but handled by OpenUpgrade:
    - account.account: user_type_id removed, replaced by account_type.
      Our module does not filter by user_type_id so no action needed.
    - account.analytic.account: analytic plans introduced. Existing analytic
      account records are migrated by OpenUpgrade to a default plan.
      The analytic_account_id Many2one on budget lines remains valid.
    """
    openupgrade.logged_query(
        env.cr,
        """
        SELECT COUNT(*)
        FROM account_move_budget
        """,
    )
    row = env.cr.fetchone()
    _logger.info("account_move_budget: %s budget records found, migration OK.", row[0])
