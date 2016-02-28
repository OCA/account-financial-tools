# -*- coding: utf-8 -*-
# © 2015 ONESTEiN BV (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _default_cost_center(self):
        return self._context.get('cost_center_id') \
            or self.env['account.cost.center']

    cost_center_id = fields.Many2one(
        'account.cost.center', string='Cost Center',
        default=_default_cost_center)

    @api.model
    def move_line_get_item(self, line):
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        if line.cost_center_id:
            res['cost_center_id'] = line.cost_center_id.id
        return res
