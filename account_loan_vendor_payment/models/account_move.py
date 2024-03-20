from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    loans_count = fields.Integer(
        compute="_compute_get_loans_count", string="Number of Loans"
    )

    def _compute_get_loans_count(self):
        payments = self.env["account.payment"]
        for rec in self:
            rec.loans_count = len(
                payments.search([("reconciled_bill_ids", "=", rec.id)]).mapped(
                    "loan_id"
                )
            )

    def get_loans(self):
        payments = self.env["account.payment"]
        loan_ids = payments.search([("reconciled_bill_ids", "=", self.id)]).mapped(
            "loan_id"
        )
        action = {
            "type": "ir.actions.act_window",
            "name": "Loans",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "account.loan",
            "domain": [("id", "in", loan_ids.ids)],
        }
        return action

    def action_register_payment(self):
        res = super().action_register_payment()
        if len(self.mapped("currency_id")) > 1:
            res["context"].update(
                {
                    "default_check_bills_currency": True,
                }
            )
        return res
