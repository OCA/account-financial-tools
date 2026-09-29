# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    clearance_plan_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Default Clearance Plan Journal",
        help="The journal used by default on clearance plans.",
    )
    clearance_plan_move_line_name = fields.Char(
        string="Default Clearance Plan Move Line Name",
        help="Default name that will be given to new open "
        "move lines created by clearance plans",
        default="Clearance Plan",
    )
