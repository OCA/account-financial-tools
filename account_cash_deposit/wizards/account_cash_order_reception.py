# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.tools.misc import format_date


class AccountCashOrderReception(models.TransientModel):
    _name = "account.cash.order.reception"
    _description = "Cash Order Reception"

    order_id = fields.Many2one(
        "account.cash.deposit", readonly=True, string="Cash Order"
    )
    date = fields.Date(
        string="Cash Reception Date", default=fields.Date.context_today, required=True
    )
    total_amount = fields.Monetary(related="order_id.total_amount")
    currency_id = fields.Many2one(related="order_id.currency_id")

    def run(self):
        self.ensure_one()
        self.order_id.message_post(
            body=_("Cash reception confirmed on %s.") % format_date(self.env, self.date)
        )
        self.order_id.validate(force_date=self.date)
