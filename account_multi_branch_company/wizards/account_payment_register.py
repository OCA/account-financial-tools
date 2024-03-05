# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_reconciled_all_moves(self, payment):
        return payment.reconciled_bill_ids + payment.reconciled_invoice_ids

    def _update_branch(self, payments):
        for payment in payments:
            reconciled_moves = self._get_reconciled_all_moves(payment)
            if len(reconciled_moves.mapped("branch_id")) > 1:
                raise UserError(
                    _(
                        "The Branch in the Bills/Invoices "
                        "to register payment must be the same."
                    )
                )
            # Update branch payment from move
            payment.branch_id = reconciled_moves.mapped("branch_id").id
            # Update JE payment from payment
            payment.move_id.branch_id = payment.branch_id
        return payments

    def _create_payments(self):
        payments = super()._create_payments()
        payments = self._update_branch(payments)
        return payments
