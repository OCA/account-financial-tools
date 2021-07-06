# Copyright 2021 ForgeFlow, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class WizAssetMoveReverse(models.TransientModel):
    _name = "wiz.asset.move.reverse"
    _description = "Reverse posted journal entry on depreciation line"

    line_id = fields.Many2one(
        comodel_name="account.asset.line",
        string="Asset Line",
        readonly=True,
        required=True,
    )
    date_reversal = fields.Date(
        string="Reversal date",
        required=True,
        default=fields.Date.context_today,
    )
    reason = fields.Char(string="Reason")
    journal_id = fields.Many2one(
        "account.journal",
        string="Use Specific Journal",
        help="If empty, uses the journal of the journal entry to be reversed.",
    )

    @api.model
    def default_get(self, fields):
        res = super(WizAssetMoveReverse, self).default_get(fields)
        line_ids = (
            self.env["account.asset.line"].browse(self.env.context["active_ids"])
            if self.env.context.get("active_model") == "account.asset.line"
            else self.env["account.asset.line"]
        )
        res["line_id"] = line_ids[0].id if line_ids else False
        return res

    def reverse_move(self):
        move = self.line_id.move_id
        move_reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=move.ids)
            .create(
                {
                    "date": fields.Date.today(),
                    "reason": self.reason,
                    "refund_method": "refund",
                    "journal_id": self.journal_id.id,
                }
            )
        )
        reversal = move_reversal.with_context(allow_asset=True).reverse_moves()
        reverse_move = self.env["account.move"].browse(reversal["res_id"])
        reverse_move.action_post()
        self.line_id.with_context(
            unlink_from_asset=True
        ).update_asset_line_after_unlink_move()
        return True
