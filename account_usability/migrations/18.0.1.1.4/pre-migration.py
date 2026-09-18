# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

from odoo.addons.account_usability.hooks import pre_init_hook


@openupgrade.migrate()
def migrate(env, version):
    pre_init_hook(env)
