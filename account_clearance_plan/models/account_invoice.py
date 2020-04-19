# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    def get_clearance_plan_wizard(self):
        account = self.mapped("account_id")
        if len(account.ids) != 1:
            raise UserError(_("Please select invoices from exactly one account."))
        move_lines = self.mapped("move_id.line_ids").filtered(
            lambda l: l.account_id == account
        )
        context = self.env.context.copy()
        context.update(
            {"active_ids": move_lines.ids, "active_model": "account.move.line"}
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.clearance.plan",
            "name": "Clearance Plan",
            "target": "new",
            "view_mode": "form",
            "context": context,
        }
