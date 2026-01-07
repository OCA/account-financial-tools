# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM ir_model_data imd
        USING date_range_type drt
        WHERE imd.model = 'date.range.type' AND imd.res_id = drt.id
            AND imd.name = 'fiscalyear'""",
    )
