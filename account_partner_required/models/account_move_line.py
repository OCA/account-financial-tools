# Copyright 2014-2022 Acsone (http://acsone.eu)
# Copyright 2016-2022 Akretion (http://www.akretion.com/)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _check_partner_required_msg(self):
        comp_cur = self.company_id.currency_id
        for line in self:
            if comp_cur.is_zero(line.debit) and comp_cur.is_zero(line.credit):
                continue
            policy = line.account_id.get_partner_policy()
            if policy == "always" and not line.partner_id:
                return _(
                    "Partner policy is set to 'Always' on account '%(account)s' but "
                    "the partner is missing on the journal item '%(move_line)s'."
                ) % {
                    "account": line.account_id.display_name,
                    "move_line": line.display_name,
                }
            elif policy == "never" and line.partner_id:
                return _(
                    "Partner policy is set to 'Never' on account '%(account)s' but "
                    "the journal item '%(move_line)s' has the partner '%(partner)s'."
                ) % {
                    "account": line.account_id.display_name,
                    "move_line": line.display_name,
                    "partner": line.partner_id.display_name,
                }

    @api.constrains("partner_id", "account_id", "debit", "credit")
    def _check_partner_required(self):
        for line in self:
            message = line._check_partner_required_msg()
            if message:
                raise ValidationError(message)
