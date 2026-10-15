# Copyright 2026 Le Filament (https://le-filament.com)
# License LGPL-3.0 (https://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    vies_vat_api = fields.Selection(
        selection=[
            ("rest", "REST API (requests)"),
            ("soap", "SOAP API (stdnum)"),
        ],
        string="VIES API",
        default="rest",
        help="Technical way used to query the EU VIES service:\n"
        "- REST API: direct HTTP call to the VIES REST endpoint.\n"
        "- SOAP API: call through the stdnum library (legacy SOAP service).",
    )
