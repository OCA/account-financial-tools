# Copyright 2021 Opener B.V. <stefan@opener.amsterdam>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    """Prevent the compute method from kicking in.

    Population of the columns is triggered in the post_init_hook
    """
    cr.execute(
        """
        alter table account_account
        add column if not exists root_group_id INTEGER,
        add column if not exists sub_group_id INTEGER;
        alter table account_move_line
        add column if not exists account_root_group_id INTEGER,
        add column if not exists account_sub_group_id INTEGER;
        """)


def post_init_hook(cr, registry):
    """Populate the columns created in the pre-init-hook
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["account.group"]._account_groups_compute()
