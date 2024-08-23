# Copyright 2024 Sodexis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_send_and_print(self):
        report_action = super().action_send_and_print()
        substitution_template = (
            self.env["mail.compose.message"]
            .sudo()
            ._get_substitution_template(
                (
                    report_action["context"]["composition_mode"]
                    if "composition_mode" in report_action["context"]
                    else "comment"
                ),
                self.env["mail.template"].browse(
                    report_action["context"]["default_mail_template_id"]
                ),
                (
                    report_action["context"]["active_ids"]
                    if "active_ids" in report_action["context"]
                    else []
                ),
            )
        )
        if substitution_template:
            report_action["context"][
                "default_mail_template_id"
            ] = substitution_template.id
        return report_action
