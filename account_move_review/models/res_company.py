# Copyright 2026 Saad Elbahi
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    restrict_move_draft_to_reviewers = fields.Boolean(
        string="Restrict Reset to Draft to Reviewers",
        default=False,
        help="When enabled, only users in the Entry Reviewer group can reset "
        "posted journal entries, invoices, bills, and payments to draft.",
    )
