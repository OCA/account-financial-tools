# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import Any

from odoo import api, models, tools


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _fill_bank_cash_dashboard_data(
        self, dashboard_data: dict[int, dict]
    ) -> dict[int, dict]:
        """Inject the custom flag used to toggle the Reconcile button."""
        super()._fill_bank_cash_dashboard_data(dashboard_data)
        if not dashboard_data:
            return dashboard_data

        is_show_reconcile_button = bool(self.env.context.get("account_dashboard"))
        toggle_ids = set(self.ids) & set(dashboard_data)
        for journal_id in toggle_ids:
            dashboard_data[journal_id]["is_show_reconcile_button"] = (
                is_show_reconcile_button
            )
        return dashboard_data

    @api.model
    @tools.ormcache()
    def _get_accounting_dashboard_action_id(self) -> int | bool:
        """Get the ID of the accounting dashboard action."""
        action = self.env.ref(
            "account_dashboard.open_account_journal_dashboard_kanban_inherit",
            raise_if_not_found=False,
        )
        return action.id if action else False

    @api.model
    def get_view(
        self, view_id: int | None = None, view_type: str = "form", **options: Any
    ) -> dict:
        """
        Method get_view to modify the dashboard view architecture.
        Removes the 'o_account_kanban' class when accessed from the custom dashboard.
        """
        res = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type != "kanban" or not res.get("arch"):
            return res

        action_id = options.get("action_id")
        try:
            action_id = int(action_id)
        except (TypeError, ValueError):
            return res

        dashboard_action_id = self._get_accounting_dashboard_action_id()
        if not dashboard_action_id or action_id != dashboard_action_id:
            return res

        res["arch"] = res["arch"].replace('class="o_account_kanban"', 'class=""')
        return res
