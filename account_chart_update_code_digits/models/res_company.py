# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_code_digits = fields.Integer()
