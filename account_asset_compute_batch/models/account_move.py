# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        if self.env.context.get("delay_post"):
            self.write({"auto_post": True})
            return False
        return super().action_post()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    compute_batch_id = fields.Many2one(
        comodel_name="account.asset.compute.batch",
        index=True,
        ondelete="set null",
        readonly=True,
    )
