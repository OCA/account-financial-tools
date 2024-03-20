from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    reconciled_bill_ids = fields.Many2many(store=True)
    loans_count = fields.Integer(
        compute="_compute_loans_count", string="Number of Loans"
    )

    loan_id = fields.Many2one("account.loan")

    def _compute_loans_count(self):
        self.loans_count = len(self.loan_id)

    def get_loans(self):
        action = {
            "type": "ir.actions.act_window",
            "name": "Loans",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.loan",
            "domain": [("id", "=", self.loan_id.id)],
        }
        return action
