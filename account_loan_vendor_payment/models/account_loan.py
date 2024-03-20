from odoo import api, fields, models


class AccountLoan(models.Model):
    _inherit = "account.loan"

    payment_ids = fields.One2many("account.payment", inverse_name="loan_id")

    @api.onchange("is_leasing")
    def _onchange_is_leasing(self):
        if "default_journal_id" not in self.env.context:
            super()._onchange_is_leasing()
