# Copyright 2026 Saad Elbahi
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    restrict_move_draft_to_reviewers = fields.Boolean(
        related="company_id.restrict_move_draft_to_reviewers",
        readonly=False,
    )
