# Copyright 2022 Le Filament
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMoveUpdateAnalytic(models.TransientModel):
    _name = "account.move.update.analytic.wizard"
    _description = "Account Move Update Analytic Account Wizard"

    line_id = fields.Many2one("account.move.line", string="Invoice line")
    current_analytic_account_id = fields.Many2one(
        related="line_id.analytic_account_id", string="Current Analytic Account"
    )
    company_id = fields.Many2one(related="line_id.company_id")
    new_analytic_account_id = fields.Many2one(
        "account.analytic.account", string="New Analytic Account", check_company=True
    )

    @api.model
    def default_get(self, fields):
        rec = super(AccountMoveUpdateAnalytic, self).default_get(fields)
        context = dict(self._context or {})
        active_id = context.get("active_id", False)
        aml = self.env["account.move.line"].browse(active_id)
        rec.update(
            {
                "line_id": active_id,
                "current_analytic_account_id": aml.analytic_account_id.id,
                "company_id": aml.company_id.id,
            }
        )
        return rec

    def update_analytic_account(self):
        self.line_id.analytic_line_ids.unlink()
        if self.new_analytic_account_id:
            self.line_id.write({"analytic_account_id": self.new_analytic_account_id.id})
            self.line_id.create_analytic_lines()
        return False
