# Copyright 2024 ForgeFlow SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging


def pre_init_hook(cr):
    """Precreate country_group_id and fill with appropriate values to prevent
    a MemoryError when the ORM attempts to call its compute method on a large
    amount of preexisting moves."""
    logger = logging.getLogger(__name__)
    logger.info(
        "Add account_move_line.country_group_id column if it does not yet exist"
    )
    cr.execute(
        "ALTER TABLE account_move_line ADD COLUMN IF NOT EXISTS country_group_id INT"
    )
    cr.execute(
        """ UPDATE account_move_line aml
            SET country_group_id = rel.res_country_group_id
            FROM res_partner rp
            JOIN res_country rc ON rp.country_id = rc.id
            JOIN res_country_res_country_group_rel rel ON rel.res_country_id = rc.id
            WHERE aml.partner_id = rp.id;
     """
    )
    logger.info("Finished adding account_move_line.country_group_id column")
