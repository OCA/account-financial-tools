# Copyright 2022 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    entry_number = fields.Char(related="move_id.entry_number")
