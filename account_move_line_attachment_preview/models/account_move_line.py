# Copyright 2023 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = "account.move.line"

    preview_attachment_id = fields.Many2one(
        string="Main Attachment",
        comodel_name="ir.attachment",
        related="move_id.message_main_attachment_id",
    )
