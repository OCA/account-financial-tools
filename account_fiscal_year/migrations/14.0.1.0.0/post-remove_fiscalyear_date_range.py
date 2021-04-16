# Copyright 2021 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Remove date ranges of type fiscal year
    fiscal_year_type = env.ref(
        "account_fiscal_year.fiscalyear", raise_if_not_found=False
    )
    if fiscal_year_type:
        openupgrade.logged_query(
            env.cr,
            """
            DELETE FROM date_range
            WHERE type_id = %s
            """,
            (fiscal_year_type.id,),
        )
