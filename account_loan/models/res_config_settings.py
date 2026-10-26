# Copyright 2026 Acsone (http://acsone.eu)
# @author Pierre Verkest <pierre@verkest.fr>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auto_post_loan_moves_at_date = fields.Boolean(
        config_parameter="account_loan.auto_post_loan_moves_at_date"
    )
