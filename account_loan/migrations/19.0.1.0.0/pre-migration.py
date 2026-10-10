# Copyright 2026 Acsone (http://acsone.eu)
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    _logger.info("Rename loan_type into loan_method (on account.loan model)")
    openupgrade.rename_fields(
        env,
        [
            ("account.loan", "account_loan", "loan_type", "loan_method"),
        ],
    )
    openupgrade.add_columns(
        env,
        [
            (
                "account.loan",
                "loan_type",
                "selection",
            )
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_loan
        SET loan_type = CASE
            WHEN is_leasing IS TRUE THEN 'leasing'
            WHEN loan_amount >= 0 THEN 'loan'
            ELSE 'borrow'
        END
        """,
    )
    openupgrade.drop_columns(env.cr, [("account_loan", "is_leasing")])
