# Copyright 2024 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    is_reversed = fields.Boolean(compute="_compute_is_reversed")

    @api.depends("reversal_move_id")
    def _compute_is_reversed(self):
        for rec in self:
            rec.is_reversed = bool(rec.reversal_move_id)

    def action_open_reversed_move(self):
        self.ensure_one()
        if not self.reversed_entry_id:
            return {}
        return {
            "name": self.reversed_entry_id.name,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "views": [[False, "form"]],
            "res_model": "account.move",
            "res_id": self.reversed_entry_id.id,
        }

    def action_open_reversal_moves(self):
        self.ensure_one()
        if not self.reversal_move_id:
            return {}
        if len(self.reversal_move_id) == 1:
            return {
                "name": self.reversal_move_id.name,
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "views": [[False, "form"]],
                "res_model": "account.move",
                "res_id": self.reversal_move_id.id,
            }
        return {
            "name": _("Journal Entries"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "search_view_id": [
                self.env.ref("account.view_account_move_filter").id,
                "search",
            ],
            "views": [
                (self.env.ref("account.view_move_tree").id, "tree"),
                (False, "form"),
            ],
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.reversal_move_id.ids)],
        }
