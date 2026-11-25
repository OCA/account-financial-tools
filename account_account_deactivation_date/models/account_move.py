# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _deprecated_lines_are_in_validity(self):
        """Return whether every deprecated line of this move is still in validity.

        A move with no deprecated line does not need the core bypass.
        """
        self.ensure_one()
        deprecated_lines = self.line_ids.filtered("account_id.deprecated")
        return bool(deprecated_lines) and all(
            line._is_deprecated_account_in_validity() for line in deprecated_lines
        )

    def _post(self, soft=True):
        """Skip the core deprecated check per move, not for the whole batch.

        ``action_post`` posts every selected move in one call. A move whose
        deprecated lines are still inside the deactivation date must not lose
        that bypass because another move in the batch is deprecated without a
        date. A mixed batch still fails as a whole: the request rolls back
        when the remaining moves are rejected.
        """
        bypass = self.filtered(lambda move: move._deprecated_lines_are_in_validity())
        if not bypass:
            return super()._post(soft=soft)
        posted = super(
            AccountMove,
            bypass.with_context(skip_account_deprecation_check=True),
        )._post(soft=soft)
        others = self - bypass
        if others:
            posted |= super(AccountMove, others)._post(soft=soft)
        return posted
