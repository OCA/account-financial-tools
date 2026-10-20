# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    truncate_subtotal = fields.Boolean(
        help="If checked, sale documents for this partner compute the line "
        "subtotal by truncating the extra decimals instead of rounding "
        "them, as required by this partner's sale condition.",
    )
