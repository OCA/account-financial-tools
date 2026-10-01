# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAccountModificationReasonWizard(models.TransientModel):
    """Ask the modification reason when saving a used account"""

    _name = "account.account.modification.reason.wizard"
    _description = "Account Modification Reason Wizard"

    reason_id = fields.Many2one(
        comodel_name="account.account.modification.reason",
        string="Reason for account modification",
        required=True,
    )
