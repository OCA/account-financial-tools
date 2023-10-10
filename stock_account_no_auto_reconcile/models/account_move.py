# Copyright 2022 ForgeFlow S.L. (http://www.forgeflow.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _stock_account_anglo_saxon_reconcile_valuation(self, product=False):
        """Warning! Overpassing an standard method, avoiding reconciling interim
        account JE. Pass the context to overpass
        """
        if self.company_id.anglo_saxon_auto_reconcile:
            return super(
                AccountMove, self
            )._stock_account_anglo_saxon_reconcile_valuation()
