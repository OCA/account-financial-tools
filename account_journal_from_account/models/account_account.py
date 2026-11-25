# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from typing import Any

from odoo import models
from odoo.exceptions import ValidationError
from odoo.tools import html_escape


class AccountAccount(models.Model):
    _inherit = "account.account"

    def action_create_journal(self) -> dict[str, Any] | None:
        """Create bank journals for selected accounts.

        Performance optimizations:
        - Single batch query for existing journals
        - Efficient validation before processing
        """
        # Validate account types early
        invalid_accounts = self.filtered(lambda acc: acc.account_type != "asset_cash")
        if invalid_accounts:
            raise ValidationError(
                self.env._(
                    "You can create 'Bank' journal from 'Bank and Cash' "
                    "type accounts only!"
                )
            )

        warning_msg_dict = self._get_existing_journals_warning()

        if warning_msg_dict:
            return self._show_confirmation_wizard(warning_msg_dict)
        return self.create_bank_journal()

    def _get_existing_journals_warning(self) -> dict[Any, list[str]]:
        """Check for existing bank journals using the selected accounts.

        Performance optimization:
        - Single batch query for all journals
        - Dictionary-based grouping for efficient lookup
        """
        warning_dict = {}

        existing_journals = self.env["account.journal"].search(
            [
                ("type", "=", "bank"),
                ("default_account_id", "in", self.ids),
            ]
        )

        journals_by_account = {}
        for journal in existing_journals:
            account = journal.default_account_id
            if account not in journals_by_account:
                journals_by_account[account] = []
            journals_by_account[account].append(journal)

        for account in self:
            if account in journals_by_account:
                warning_dict[account] = [
                    f"{j.name} " for j in journals_by_account[account]
                ]
        return warning_dict

    def _show_confirmation_wizard(
        self, warning_dict: dict[Any, list[str]]
    ) -> dict[str, Any]:
        """Display confirmation wizard with existing journals warning."""
        error_msg_parts = [
            "Existing 'Bank' journals found in system for the following "
            "selected accounts:<br/><br/>"
        ]
        for account, journal_data in warning_dict.items():
            error_msg_parts.append(
                f"<strong>{html_escape(account.display_name)}</strong><br/>"
            )
            for data in journal_data:
                error_msg_parts.append(
                    f"&nbsp;&nbsp;&nbsp;&nbsp;<strong>{html_escape(data)}</strong><br/>"
                )
            error_msg_parts.append("<br/>")

        error_msg = "".join(error_msg_parts)

        return {
            "name": self.env._("Confirmation"),
            "type": "ir.actions.act_window",
            "res_model": "user.confirmation.wizard",
            "view_mode": "form",
            "view_id": self.env.ref(
                "account_journal_from_account.view_user_confirmation_wizard_form"
            ).id,
            "target": "new",
            "context": {
                "default_message": (
                    f"{error_msg}<br/>Are you sure you want to proceed?"
                ),
                "active_model": self._name,
                "active_ids": self.ids,
                "continue_action": "create_bank_journal",
            },
        }

    def create_bank_journal(self) -> dict[str, Any]:
        """Create bank journals for all accounts in batch.

        Performance optimization:
        - Use create_multi for batch journal creation
        """
        vals_list = [
            {
                "name": rec.name,
                "type": "bank",
                "default_account_id": rec.id,
            }
            for rec in self
        ]

        bank_journal_ids = self.env["account.journal"].create(vals_list)

        action_vals = {
            "name": self.env._("Journals"),
            "type": "ir.actions.act_window",
            "res_model": "account.journal",
        }

        if len(bank_journal_ids) > 1:
            action_vals.update(
                {
                    "view_mode": "list,form",
                    "domain": [("id", "in", bank_journal_ids.ids)],
                }
            )
        else:
            action_vals.update(
                {
                    "view_mode": "form",
                    "res_id": bank_journal_ids.id,
                }
            )

        return action_vals
