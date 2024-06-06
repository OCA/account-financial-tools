# Copyright 2014-2022 Acsone (http://acsone.eu)
# Copyright 2016-2022 Akretion (http://www.akretion.com/)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    # No default value here ; only set one on account.account.type
    partner_policy = fields.Selection(
        [
            ("optional", "Optional"),
            ("always", "Always"),
            ("never", "Never"),
        ],
        help="Set the policy for the partner field:\nif you select "
        "'Optional', the accountant is free to put a partner "
        "on journal items with this account ;\n"
        "if you select 'Always', the accountant will get an error "
        "message if there is no partner ;\nif you select 'Never', "
        "the accountant will get an error message if a partner "
        "is present.",
    )

    def get_partner_policy(self):
        self.ensure_one()
        return self.partner_policy
