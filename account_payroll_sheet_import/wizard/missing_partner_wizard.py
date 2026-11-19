# Copyright 2025 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MissingPartnerWizard(models.TransientModel):
    _name = "missing.partner.wizard"
    _description = "Missing Employees from Payroll Import"

    missing_ids = fields.Text("Missing IDs")
