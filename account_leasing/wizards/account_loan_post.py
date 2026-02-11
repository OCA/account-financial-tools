# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class AccountLoanPost(models.TransientModel):
    _inherit = "account.loan.post"

    @api.model
    def _get_default_account_from_loan(self, loan):
        if loan.loan_type == "leasing":
            return loan.leased_asset_account_id.id
        return super()._get_default_account_from_loan(loan)
