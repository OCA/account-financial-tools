# -*- coding: utf-8 -*-
# Copyright 2015 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cost_center_id = fields.Many2one(
        'account.cost.center',
        string='Cost Center')
