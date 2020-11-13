# Copyright 2014-2020 Acsone (http://acsone.eu)
# Copyright 2016-2020 Akretion (http://www.akretion.com/)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountAccountType(models.Model):
    _inherit = "account.account.type"

    partner_policy = fields.Selection(
        "_partner_policy_selection",
        string="Policy for Partner Field",
        default="optional",
        help="Set the policy for the partner field :\nif you select "
        "'Optional' or leave empty, the accountant is free to put a partner "
        "on an account move line with this type of account ;\n"
        "if you select 'Always', the accountant will get an error "
        "message if there is no partner ;\nif you select 'Never', "
        "the accountant will get an error message if a partner "
        "is present.",
    )

    @api.model
    def _partner_policy_selection(self):
        return [
            ("optional", _("Optional")),
            ("always", _("Always")),
            ("never", _("Never")),
        ]


class AccountAccount(models.Model):
    _inherit = "account.account"

    # No default value here ; only set one on account.account.type
    partner_policy = fields.Selection(
        "_partner_policy_selection",
        string="Policy for Partner Field",
        help="Set the policy for the partner field :\nif you select "
        "'Optional', the accountant is free to put a partner "
        "on an account move line with this account ;\n"
        "if you select 'Always', the accountant will get an error "
        "message if there is no partner ;\nif you select 'Never', "
        "the accountant will get an error message if a partner "
        "is present ;\nif empty, the policy will be read from the "
        "type of account.",
    )

    @api.model
    def _partner_policy_selection(self):
        return self.env["account.account.type"]._partner_policy_selection()

    def get_partner_policy(self):
        self.ensure_one()
        return self.partner_policy or self.user_type_id.partner_policy


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
                    "Partner policy is set to 'Always' with account '%s' but "
                    "the partner is missing in the account move line with "
                    "label '%s'."
                ) % (line.account_id.display_name, line.name)
            elif policy == "never" and line.partner_id:
                return _(
                    "Partner policy is set to 'Never' with account '%s' but "
                    "the account move line with label '%s' has a partner "
                    "'%s'."
                ) % (
                    line.account_id.display_name,
                    line.name,
                    line.partner_id.display_name,
                )

    @api.constrains("partner_id", "account_id", "debit", "credit")
    def _check_partner_required(self):
        for line in self:
            message = line._check_partner_required_msg()
            if message:
                raise ValidationError(message)
