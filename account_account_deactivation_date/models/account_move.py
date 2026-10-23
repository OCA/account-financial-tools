# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        moves = self
        deprecated_lines = self.line_ids.filtered("account_id.deprecated")
        if deprecated_lines and all(
            line._is_deprecated_account_in_validity() for line in deprecated_lines
        ):
            moves = self.with_context(skip_account_deprecation_check=True)
        return super(AccountMove, moves)._post(soft=soft)
