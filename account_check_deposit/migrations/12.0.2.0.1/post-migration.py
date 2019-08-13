# Copyright (C) 2019-Today: GTRAP (<http://www.grap.coop/>)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(env, version):
    if not version:
        return

    # Update values for journal that can be deposited
    env.execute("""
        UPDATE account_journal
        SET can_be_deposited = true,
        deposit_debit_account_id = default_debit_account_id
        WHERE type = 'bank'
        AND bank_account_id IS NULL
    ;""")

    env.execute("""
        UPDATE account_journal
        SET can_receive_deposit = true
        WHERE type = 'bank'
        AND bank_account_id IS NOT NULL
    ;""")
