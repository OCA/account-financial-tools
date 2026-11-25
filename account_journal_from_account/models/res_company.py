# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResCompany(models.Model):
    """Extended company with payment account configuration."""

    _inherit = "res.company"

    inbound_payment_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Outstanding Receipt Account",
        check_company=True,
        help=(
            "'Outstanding Receipt Account' for manual inbound payment "
            "method line on 'bank' type journal"
        ),
    )
    outbound_payment_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Outstanding Payment Account",
        check_company=True,
        help=(
            "'Outstanding Payment Account' for manual outbound payment "
            "method line on 'bank' type journal"
        ),
    )
