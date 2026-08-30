# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import api, models
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.model
    def _get_next_account_code(self, account_type):
        """
        Compute the next sequential account code for a given account type.
        Supports both purely numeric and alphanumeric codes.
        Optimized to avoid loading all account codes into memory where possible.
        """
        if not account_type:
            return False

        type_accounts = self.search(
            [("account_type", "=", account_type), ("code", "!=", False)]
        )

        if not type_accounts:
            return False

        num_pattern = re.compile(r"\d+")
        max_num = -1
        max_code_info = None

        for record in type_accounts:
            code = record.code or ""
            matches = list(num_pattern.finditer(code))
            if matches:
                last_match = matches[-1]
                num_str = last_match.group()
                num_int = int(num_str)

                if num_int > max_num:
                    max_num = num_int
                    max_code_info = {
                        "prefix": code[: last_match.start()],
                        "num_int": num_int,
                        "suffix": code[last_match.end() :],
                        "padding": len(num_str),
                    }

        if not max_code_info:
            raise ValidationError(
                self.env._(
                    "Cannot increment code because no numeric part found in "
                    "existing accounts for this type."
                )
            )

        next_num = max_code_info["num_int"] + 1
        prefix = max_code_info["prefix"]
        suffix = max_code_info["suffix"]
        padding = max_code_info["padding"]

        while True:
            next_code = f"{prefix}{str(next_num).zfill(padding)}{suffix}"
            if not self.search([("code", "=", next_code)], limit=1):
                return next_code
            next_num += 1

    @api.onchange("account_type")
    def _onchange_account_type_set_code(self):
        """
        Auto-fill the account code when an account type is selected.
        Only sets code if it is currently empty.
        """
        for account in self:
            if account.account_type and not account.code:
                try:
                    next_code = self._get_next_account_code(account.account_type)
                    if next_code:
                        account.code = next_code
                except ValidationError as e:
                    # Optionally, show a warning instead of blocking the onchange
                    raise e
