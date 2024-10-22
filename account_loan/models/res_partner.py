# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    lended_loan_ids = fields.One2many("account.loan", inverse_name="partner_id")
    lended_loan_count = fields.Integer(
        compute="_compute_lended_loan_count",
        help="How many Loans this partner lended to us ?",
    )

    @api.depends("lended_loan_ids")
    def _compute_lended_loan_count(self):
        for record in self:
            record.lended_loan_count = len(record.lended_loan_ids)

    def action_view_partner_lended_loans(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account_loan.account_loan_action"
        )
        all_child = self.with_context(active_test=False).search(
            [("id", "child_of", self.ids)]
        )
        action["domain"] = [("partner_id", "in", all_child.ids)]
        return action
