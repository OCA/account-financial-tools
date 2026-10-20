# Copyright 2026 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Migration from 15.0 to 16.0. No structural changes."""
    openupgrade.logged_query(env.cr, "SELECT COUNT(*) FROM account_fiscal_year")
    _logger.info("account_fiscal_year: %s records, migration OK.", env.cr.fetchone()[0])
