# Copyright (C) 2025 - Today: Sylvain LE GAL (http://www.grap.coop)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _set_default_payment_accounts(self):
        account_payment_method_manual_in = self.env.ref(
            "account.account_payment_method_manual_in"
        )
        account_payment_method_manual_out = self.env.ref(
            "account.account_payment_method_manual_out"
        )
        journals = self.filtered(lambda x: x.type in ["bank", "cash"])
        for journal in journals:
            for line in journal.outbound_payment_method_line_ids.filtered(
                lambda x: x.payment_method_id == account_payment_method_manual_out
            ):
                line.payment_account_id = journal.default_account_id
            for line in journal.inbound_payment_method_line_ids.filtered(
                lambda x: x.payment_method_id == account_payment_method_manual_in
            ):
                line.payment_account_id = journal.default_account_id

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._set_default_payment_accounts()
        return res

    def write(self, vals):
        res = super().write(vals)
        if "default_account_id" in vals.keys():
            self._set_default_payment_accounts()
        return res
