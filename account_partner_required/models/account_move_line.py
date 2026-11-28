# Copyright 2014-2022 Acsone (http://acsone.eu)
# Copyright 2016-2022 Akretion (http://www.akretion.com/)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _check_partner_required_msg(self):
        self.ensure_one()
        comp_cur = self.company_id.currency_id
        if self.display_type in ("line_section", "line_note") or comp_cur.is_zero(
            self.balance
        ):
            return

        policy = self.account_id.get_partner_policy()
        if policy == "always" and not self.partner_id:
            return self.env._(
                "Partner policy is set to 'Always' on account '%(account)s' but "
                "the partner is missing on the journal item '%(move_line)s'.",
                account=self.account_id.display_name,
                move_line=self.display_name,
            )
        elif policy == "never" and self.partner_id:
            return self.env._(
                "Partner policy is set to 'Never' on account '%(account)s' but "
                "the journal item '%(move_line)s' has the partner '%(partner)s'."
            ) % {
                "account": self.account_id.display_name,
                "move_line": self.display_name,
                "partner": self.partner_id.display_name,
            }
