# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAccountModificationReason(models.Model):
    _name = "account.account.modification.reason"
    _description = "Account Modification Reason"
    _order = "sequence, name"

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
