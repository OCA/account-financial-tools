# Copyright 2015-2020 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountCostCenter(models.Model):
    _name = "account.cost.center"
    _description = "Account Cost Center"

    name = fields.Char(string="Title", required=True)
    code = fields.Char(required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
