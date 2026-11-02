# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date

from odoo.addons.account.models.account_move import BYPASS_LOCK_CHECK


class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_fiscal_lock_dates(self):
        res = super()._check_fiscal_lock_dates()
        if self.env.context.get("bypass_lock_check") is BYPASS_LOCK_CHECK:
            return res
        for move in self:
            if not move.date:
                continue
            locked_accounts = move.line_ids.account_id.filtered_domain(
                [("lock_to_date", "<=", move.date)]
            )
            if locked_accounts:
                account = locked_accounts[0]
                raise UserError(
                    self.env._(
                        "Account '%(account)s' is locked from %(lock_to_date)s "
                        "(included)",
                        account=account.display_name,
                        lock_to_date=format_date(self.env, account.lock_to_date),
                    )
                )
        return res
