# Copyright (C) 2023 AKRETION
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(env, version):
    if not version:
        return

    env.execute("""
    ALTER TABLE account_move DROP CONSTRAINT IF EXISTS account_move_name_state_diagonal ;
    """)
