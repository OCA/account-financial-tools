# -*- coding: utf-8 -*-
# Copyright 2015-2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _default_cost_center(self):
        return self.env['account.cost.center'].browse(
            self._context.get('cost_center_id'))

    cost_center_id = fields.Many2one(
        'account.cost.center',
        string='Cost Center',
        default=_default_cost_center
    )

    @api.model
    def move_line_get_item(self, line):
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        if line.cost_center_id:
            res['cost_center_id'] = line.cost_center_id.id
        return res
