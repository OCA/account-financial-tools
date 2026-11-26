# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import UserError


class AccountLoanIncreaseAmount(models.TransientModel):
    _inherit = "account.loan.increase.amount"

    @api.model
    def _get_default_account_from_loan(self, loan):
        if loan.loan_type == "leasing":
            return loan.leased_asset_account_id.id
        return super()._get_default_account_from_loan(loan)

    def _pre_loan_increase_check(self):
        if self.loan_id.loan_type == "leasing":
            if self.loan_id.line_ids.filtered(
                lambda r: r.date <= self.date and not r.move_ids
            ):
                raise UserError(self.env._("Some invoices are not created"))
            if self.loan_id.line_ids.filtered(
                lambda r: r.date > self.date and r.move_ids
            ):
                raise UserError(self.env._("Some future invoices already exists"))
            return
        return super()._pre_loan_increase_check()
