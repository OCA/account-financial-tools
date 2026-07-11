# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html
from openupgradelib import openupgrade


def pre_init_hook(env):
    """Add menu_finance also as xmlid for account_usability
    so that it get listed in i18n/account_usability.pot
    automatically and can be translated with the default workflow
    """
    menu_finance = env.ref("account.menu_finance")
    openupgrade.add_xmlid(
        env.cr, "account_usability", "menu_finance", "ir.ui.menu", menu_finance.id
    )


def post_init_hook(env):
    """Ensure translation is getting overwritten on install
    by default this isn't the case, because on a normal install
    no i18n-overwrite is passed"""
    module = env.ref("base.module_account_usability")
    module._update_translations(overwrite=True)
