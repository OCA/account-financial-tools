# -*- coding: utf-8 -*-
# © 2015 ONESTEiN BV (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class AccountCostCenter(models.Model):
    _name = 'account.cost.center'
    _description = 'Account Cost Center'

    name = fields.Char(string='Title', required=True, size=64)
    code = fields.Char(string='Code', required=True, size=16)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id)
