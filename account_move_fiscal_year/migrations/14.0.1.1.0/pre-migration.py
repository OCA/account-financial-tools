# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    # move fields from account_invoice_line
    field_spec = [
        (
            "date_range_fy_id",
            "account.move",
            False,
            "many2one",
            False,
            "account_move_fiscal_month",
        )
    ]
    openupgrade.add_fields(env, field_spec)
    query = """
        update account_move am
        set date_range_fy_id = data.fiscal_year
        FROM (
        select am.id as move_id,
            fy.id as fiscal_year
        from account_move am
        join account_fiscal_year fy
            on  fy.company_id = am.company_id
            and am.date between fy.date_from and fy.date_to
        )
        as data
        where am.id = data.move_id
    """
    openupgrade.logged_query(env.cr, query)
