# Copyright (C) 2025 - Today: Sylvain LE GAL (http://www.grap.coop)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    journals = (
        env["account.journal"]
        .with_context(active_test=False)
        .search([("type", "in", ["bank", "cash"])])
    )
    for journal in journals:
        _logger.info(
            f"Initialize default accounts for journal '{journal.code} - {journal.name}'"
        )
        journal._set_default_payment_accounts()
