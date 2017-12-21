# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import odoo

_logger = logging.getLogger(__name__)


def recompute_asset_line_values(env):
    # Fields (remaining/depreciated_value) changed from integer to float
    _logger.info("Updating asset lines remaining/depreciated value")
    assets = env['account.asset'].with_context(
        allow_asset_line_update=True
    ).search([])
    for asset in assets:
        if asset.depreciation_line_ids:
            asset.depreciation_line_ids.sorted(
                lambda rec: rec.line_date
            )[0]._compute()


def migrate(cr, version):
    if not version:
        # installation of the module
        return
    with odoo.api.Environment.manage():
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        recompute_asset_line_values(env)
