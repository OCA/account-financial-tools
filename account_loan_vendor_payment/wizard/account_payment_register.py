from odoo import _, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_default_loan_journal_currency_id(self):
        return self.env.company.currency_id.id

    loan_payment = fields.Boolean("Open Loan", default=False)
    check_bills_currency = fields.Boolean(default=False)
    loan_journal_id = fields.Many2one(
        "account.journal",
        domain="[('company_id', '=', company_id), ('type', '=', 'general')]",
    )
    exchange_rate = fields.Float(default=1)
    loan_journal_currency_id = fields.Many2one(
        related="loan_journal_id.currency_id", string="Loan journal currency"
    )

    def action_create_payments(self):
        if not self.loan_payment:
            return super().action_create_payments()
        payments = self._create_payments()
        amount = self.amount * self.exchange_rate if self.exchange_rate else self.amount
        action = {
            "name": _("Open Vendor Loan"),
            "view_mode": "form",
            "type": "ir.actions.act_window",
            "res_model": "account.loan",
            "context": {
                "default_move_ids": self.env["account.move"]
                .browse(self._context.get("active_ids"))
                .ids,
                "default_loan_amount": amount,
                "default_journal_id": self.loan_journal_id.id,
                "default_payment_ids": payments.ids,
            },
        }
        return action
