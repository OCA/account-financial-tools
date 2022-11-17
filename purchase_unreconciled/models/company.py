# Copyright 2019-21 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    purchase_reconcile_account_id = fields.Many2one(
        "account.account",
        domain=lambda self: [("deprecated", "=", False)],
        string="Write-Off Account On Purchases",
        ondelete="restrict",
        copy=False,
        help="Write-off account to reconcile Unreconciled Purchase Orders",
    )
    purchase_reconcile_journal_id = fields.Many2one(
        "account.journal", string="WriteOff Journal for Purchases"
    )
    purchase_lock_auto_reconcile = fields.Boolean()
    purchase_reconcile_tolerance = fields.Float(
        string="Purchase Reconcile Tolerance (%)",
        default=0.0,
        help="Percentage of tolerance of residual amount vs total amount of the "
        "Purchase Order. Leave zero to accept all discrepancies",
    )
