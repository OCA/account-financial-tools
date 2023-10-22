# Copyright 2014-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CreditControlPolicy(models.Model):
    """ADD dunning fees fields"""

    _inherit = "credit.control.policy.level"

    dunning_product_id = fields.Many2one("product.product", string="Fees Product")

    dunning_fixed_amount = fields.Float(string="Fees Fixed Amount")

    dunning_currency_id = fields.Many2one(
        "res.currency",
        string="Fees currency",
        help="Currency of the dunning fees. If empty, it takes the "
        "company's currency.",
    )

    # planned type are fixed, percent, compound
    dunning_fees_type = fields.Selection(
        [("fixed", "Fixed")], string="Type", default="fixed"
    )
