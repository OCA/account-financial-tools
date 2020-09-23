# Copyright 2020 Ecosoft (http://ecosoft.co.th)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountMoveTemplate(models.Model):
    _inherit = "account.move.template"


class AccountMoveTemplateLine(models.Model):
    _inherit = "account.move.template.line"

    opt_account_id = fields.Many2one(
        "account.account",
        string="Account Opt.",
        domain=[("deprecated", "=", False)],
        help="When amount is negative, use this account in stead",
    )
