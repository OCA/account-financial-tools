# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountSpreadLinkMoveLine(models.TransientModel):
    _name = "account.spread.link.move.line"
    _description = "Link spread cost/revenue sheet with journal item"

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Journal Entry",
        required=True,
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Journal Item",
        domain="[('move_id', '=', move_id), ('spread_id', '=', False)]",
        required=True,
    )

    @api.onchange("move_id")
    def _onchange_move_id(self):
        self.move_line_id = False

    def link_move_line(self):
        active_id = self.env.context.get("active_id")
        spread = self.env["account.spread"].browse(active_id)
        if spread.invoice_line_id:
            raise UserError(
                _(
                    "Already linked with a journal item, please unlink the existing one first."
                )
            )
        spread.invoice_line_id = self.move_line_id
