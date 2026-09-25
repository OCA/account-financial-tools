# Copyright 2026 Acsone (http://acsone.eu)
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# If you are comming from Odoo Version < 19.0
# you will needs account_leasing module installed as
# code was extracted while moving from v18 to v19
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    leasing_module = env["ir.module.module"].search([("name", "=", "account_leasing")])
    if not leasing_module.exists():
        env.cr.execute("SELECT 1 FROM account_loan WHERE loan_type = 'leasing' LIMIT 1")
        if env.cr.fetchone():
            raise RuntimeError(
                "Found existing leasing records in account.loan, but account_leasing "
                "module is not available in addons path. Please add account_leasing to "
                "your addons path to complete the migration."
            )
        _logger.warning(
            "account_leasing module not found in odoo path. Related features "
            "were in account_loan in previous version, consider to install it "
            "or cleanup extra fields"
        )
        return
    _logger.info(
        "Installing account_leasing as that feature were previously part of "
        "account_loan..."
    )
    leasing_module.button_install()
