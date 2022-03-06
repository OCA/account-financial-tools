# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Update account move lines with sale order line")
    cr.execute(
        """
        UPDATE account_move_line aml SET sale_line_id = sm.sale_line_id
        FROM account_move_line aml2
        INNER JOIN account_move am
        ON am.id = aml2.move_id
        INNER JOIN stock_move sm ON
        am.stock_move_id = sm.id
        WHERE aml.id = aml2.id
        AND sm.sale_line_id IS NOT NULL;
    """
    )
