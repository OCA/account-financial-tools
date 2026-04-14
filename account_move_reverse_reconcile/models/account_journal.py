# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models

from .account_move import REVERSAL_POST_AUTOMATIC_RECONCILE_VALUES


class AccountJournal(models.Model):
    _inherit = "account.journal"

    reversal_post_automatic_reconcile_default = fields.Selection(
        REVERSAL_POST_AUTOMATIC_RECONCILE_VALUES,
        default="reconcile",
        required=True,
        string="Automatic reconciliation on posting of reversal moves",
        help="Default value to apply on reversal moves created in this journal.",
    )
