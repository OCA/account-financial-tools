# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.fields import Domain


class AccountLoanGenerateWizard(models.TransientModel):
    _inherit = "account.loan.generate.wizard"

    loan_type = fields.Selection(
        [("leasing", "Leasings"), ("loan", "Loans")], required=True, default="loan"
    )

    def _run_leasing(self):
        created_ids = self.env["account.loan"]._generate_leasing_entries(self.date)
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        if len(created_ids) == 0:
            return
        result["domain"] = Domain("id", "in", created_ids)
        return result

    def run(self):
        self.ensure_one()
        if self.loan_type == "leasing":
            return self._run_leasing()
        return super().run()
