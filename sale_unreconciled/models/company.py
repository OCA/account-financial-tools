# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_reconcile_account_id = fields.Many2one(
        "account.account",
        domain=lambda self: [("deprecated", "=", False)],
        string="Write-Off Account On Sales",
        ondelete="restrict",
        copy=False,
        help="Write-off account to reconcile Unreconciled Sale Orders",
    )

    sale_reconcile_journal_id = fields.Many2one(
        "account.journal", string="Writeoff Journal for Sales"
    )
    sale_lock_auto_reconcile = fields.Boolean()
