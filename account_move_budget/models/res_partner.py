# Copyright 2024 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    budget_count = fields.Integer(
        "# Budgets", compute="_compute_budget_count", compute_sudo=False
    )

    def _get_budget_ids(self):
        self.ensure_one()
        budget_lines = self.env["account.move.budget.line"].search(
            [("partner_id", "=", self.id)]
        )
        return budget_lines.mapped("budget_id.id")

    def _compute_budget_count(self):
        for partner in self:
            partner.budget_count = len(partner._get_budget_ids())

    def action_view_budget(self):
        self.ensure_one()
        budget_ids = self._get_budget_ids()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account_move_budget.account_move_budget_act_window"
        )
        action["domain"] = [("id", "in", budget_ids)]
        return action
