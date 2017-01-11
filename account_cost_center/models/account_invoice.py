# -*- coding: utf-8 -*-
# Copyright 2015-2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    cost_center_id = fields.Many2one(
        'account.cost.center',
        string='Cost Center',
        help='Default Cost Center'
    )

    @api.model
    def line_get_convert(self, line, part, date):
        res = super(AccountInvoice, self).line_get_convert(line, part, date)
        if line.get('cost_center_id'):
            res['cost_center_id'] = line['cost_center_id']
        return res
