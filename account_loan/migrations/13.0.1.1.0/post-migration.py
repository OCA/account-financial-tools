# Copyright 2021 Creu Blanca - Alba Riera

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET loan_line_id = ai.loan_line_id,
            loan_id = ai.loan_id
        FROM account_invoice ai
        WHERE ai.id = am.old_invoice_id and ai.loan_id is not null""",
    )
