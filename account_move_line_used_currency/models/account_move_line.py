# Copyright 2021 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    amount_used_currency = fields.Monetary(
        string="Amount (Used Currency)",
        compute="_compute_used_currency",
        store=True,
        help="This amount is the foreign amount currency, if used, and the "
        "company currency, if no foreign currency is used. It's purpose"
        "is to allow reporting on journal items combining foreign "
        "and company currencies.",
    )
    used_currency_id = fields.Many2one(
        "res.currency",
        string="Used Currency",
        compute="_compute_used_currency",
        store=True,
        help="Used currency of the journal item. It is the foreign currency, "
        "or the company currency, where the foreign currency has not "
        "been used.",
    )

    @api.depends(
        "currency_id", "company_currency_id", "debit", "credit", "amount_currency"
    )
    def _compute_used_currency(self):
        for rec in self:
            if rec.currency_id:
                rec.amount_used_currency = rec.amount_currency
                rec.used_currency_id = rec.currency_id
            else:
                rec.amount_used_currency = rec.balance
                rec.used_currency_id = rec.company_currency_id
