# Copyright 2024 Sodexis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMoveSendWizard(models.TransientModel):
    _inherit = "account.move.send.wizard"

    @api.depends("move_id")
    def _compute_mail_template_id(self):
        res = super()._compute_mail_template_id()

        composer = self.env["mail.compose.message"].sudo()

        for wizard in self:
            if not wizard.mail_template_id:
                continue

            substitution_template = composer._get_substitution_template(
                "comment",
                wizard.mail_template_id,
                [wizard.move_id.id],
            )

            if substitution_template:
                wizard.mail_template_id = substitution_template

        return res
