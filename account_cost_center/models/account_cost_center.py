# -*- coding: utf-8 -*-
# Copyright 2015-2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class AccountCostCenter(models.Model):
    _name = 'account.cost.center'
    _description = 'Account Cost Center'

    name = fields.Char(string='Title', required=True)
    code = fields.Char(required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id
    )
