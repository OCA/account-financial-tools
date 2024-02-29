# Copyright 2023 Engenere - Antônio S. P. Neto
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_rename_columns = {
    "res_company": [("auto_archive", "auto_archive_spread")],
    "account_spread": [("invoice_line_id", None)],
}


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_columns(env.cr, _rename_columns)
