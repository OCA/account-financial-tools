# Copyright 2021 Opener B.V. <stefan@opener.amsterdam>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    anglo_saxon_accounting = fields.Boolean(
        related="company_id.anglo_saxon_accounting",
        readonly=False,
        string="Use anglo-saxon accounting",
        help=(
            "Record the cost of a good as an expense when this good is "
            "invoiced to a final customer."
        ),
    )
