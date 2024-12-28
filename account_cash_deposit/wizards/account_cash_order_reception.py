# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
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

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res["order_id"] = self._context.get("active_id")
        assert self._context.get("active_model") == "account.cash.deposit"
        return res

    def run(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        if self.date > today:
            raise UserError(
                _("The Cash Reception Date (%s) is in the future.")
                % format_date(self.env, self.date)
            )
        self.order_id.message_post(
            body=_("Cash reception confirmed on %s.") % format_date(self.env, self.date)
        )
        self.order_id.validate(force_date=self.date)
