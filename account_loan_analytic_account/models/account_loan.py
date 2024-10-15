# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountLoan(models.Model):
    _name = "account.loan"
    _inherit = ["account.loan", "analytic.mixin"]
