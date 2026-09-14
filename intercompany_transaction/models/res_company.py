# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    intercompany_transaction_config_ids = fields.One2many(
        "intercompany.transaction.config",
        "from_company_id",
        string="Intercompany Transaction Config",
        help="Configuration for intercompany transactions from this company",
    )
