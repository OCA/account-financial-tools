# Copyright 2021 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging

try:
    from openupgradelib import openupgrade
except Exception:
    from odoo.tools import sql as openupgrade

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    _logger.info("Pre-creating column amount_used_currency for table account_move_line")
    if not openupgrade.column_exists(cr, "account_move_line", "amount_used_currency"):
        cr.execute(
            """
            ALTER TABLE account_move_line
            ADD COLUMN amount_used_currency float;
            COMMENT ON COLUMN account_move_line.amount_used_currency
            IS 'Amount (Used Currency)';
            """
        )
    _logger.info("Pre-creating column used_currency_id for table account_move_line")
    if not openupgrade.column_exists(cr, "account_move_line", "used_currency_id"):
        cr.execute(
            """
            ALTER TABLE account_move_line
            ADD COLUMN used_currency_id INTEGER;
            COMMENT ON COLUMN account_move_line.used_currency_id
            IS 'Used Currency';
            """
        )
    _logger.info(
        "Pre-computing the value of amount_used_currency "
        "and used_currency_id to speed up the installation"
    )
    cr.execute(
        """
        UPDATE account_move_line
        SET amount_used_currency = balance,
        used_currency_id = company_currency_id
        WHERE currency_id IS NULL;
        """
    )
    cr.execute(
        """
        UPDATE account_move_line
        SET amount_used_currency = amount_currency,
        used_currency_id = currency_id
        WHERE currency_id IS NOT NULL;
        """
    )
