# -*- coding: utf-8 -*-
# Copyright 2015-2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    cost_center_id = fields.Many2one(
        'account.cost.center',
        string='Cost Center'
    )
