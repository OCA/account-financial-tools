# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging


def pre_init_hook(cr):
    """Precreate account_internal_group and fill with appropriate values to prevent
    a MemoryError when the ORM attempts to call its compute method on a large
    amount of preexisting moves."""
    logger = logging.getLogger(__name__)
    logger.info(
        "Add account_move_line.account_internal_group column if it does not yet exist"
    )
    cr.execute(
        "ALTER TABLE account_move_line ADD COLUMN IF NOT EXISTS account_internal_group VARCHAR"
    )
    cr.execute(
        """ UPDATE account_move_line aml0 SET account_internal_group = aa.internal_group
        FROM account_move_line aml
        INNER JOIN account_account aa ON aa.id = aml.account_id
        WHERE aml.id = aml0.id
        AND aml.account_internal_group IS NULL
     """
    )
    logger.info("Finished adding account_move_line.account_internal_group column")
