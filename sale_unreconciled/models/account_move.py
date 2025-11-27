from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_writeoff = fields.Boolean()
