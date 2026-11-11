# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _is_account_deactivated(self):
        """Return whether the line is dated on or after the account deactivation."""
        self.ensure_one()
        deactivation_date = self.account_id.deactivation_date
        return bool(deactivation_date and self.date and self.date >= deactivation_date)

    def _is_deprecated_account_in_validity(self):
        """Return whether the account is deprecated but valid at the line date."""
        self.ensure_one()
        deactivation_date = self.account_id.deactivation_date
        return bool(
            self.account_id.deprecated
            and deactivation_date
            and self.date
            and self.date < deactivation_date
        )

    def _check_constrains_account_id_journal_id(self):
        lines = self.filtered(
            lambda line: line.display_type not in ("line_section", "line_note")
        )
        if not self.env.context.get("skip_account_deactivation_check"):
            for line in lines:
                if line._is_account_deactivated():
                    raise UserError(
                        _(
                            "The account %(account)s is inactive since %(date)s "
                            "and cannot be used in entries dated %(line_date)s.",
                            account=line.account_id.display_name,
                            date=format_date(
                                self.env, line.account_id.deactivation_date
                            ),
                            line_date=format_date(self.env, line.date),
                        )
                    )
        in_validity = lines.filtered(
            lambda line: line._is_deprecated_account_in_validity()
        )
        if in_validity:
            super(
                AccountMoveLine,
                in_validity.with_context(skip_account_deprecation_check=True),
            )._check_constrains_account_id_journal_id()
        return super(
            AccountMoveLine, self - in_validity
        )._check_constrains_account_id_journal_id()
