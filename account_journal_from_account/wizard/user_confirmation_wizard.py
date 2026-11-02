# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import Any

from odoo import fields, models


class UserConfirmationWizard(models.TransientModel):
    """Wizard for user confirmations with dynamic action execution."""

    _name = "user.confirmation.wizard"
    _description = "User Confirmation Wizard"

    message = fields.Html(string="Confirmation Message", sanitize=False, required=True)

    def action_confirm(self) -> dict[str, Any]:
        """Execute the configured action on confirmation."""
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids")
        action_function = self.env.context.get("continue_action")
        action_context = self.env.context.get("action_context", {})

        if active_model and active_ids and action_function:
            records = self.env[active_model].browse(active_ids)
            return getattr(records.with_context(**action_context), action_function)()

        return {"type": "ir.actions.act_window_close"}

    def action_cancel(self) -> dict[str, Any]:
        """Close the wizard without action."""
        return {"type": "ir.actions.act_window_close"}
