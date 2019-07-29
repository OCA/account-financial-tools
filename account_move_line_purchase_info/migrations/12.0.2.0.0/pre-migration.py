# Copyright 2019 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging


_logger = logging.getLogger(__name__)

__name__ = "Upgrade to 12.0.2.0.0"


def update_purchase_id_column(cr):
    cr.execute("""SELECT column_name
    FROM information_schema.columns
    WHERE table_name='account_move_line' AND
    column_name='purchase_id'""")
    if not cr.fetchone():
        _logger.info("""Add column purchase_id to account_move_line""")
        cr.execute(
            """
            ALTER TABLE account_move_line ADD COLUMN purchase_id integer;
            """)
    _logger.info("""Updating values for purchase_id in account_move_line""")
    cr.execute(
        """
        UPDATE account_move_line aml
        SET purchase_id = pol.order_id
        FROM purchase_order_line AS pol
        WHERE aml.purchase_line_id = pol.id
        """
    )


def migrate(cr, version):
    if not version:
        return
    update_purchase_id_column(cr)
