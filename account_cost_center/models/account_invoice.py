# Copyright 2015-2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    cost_center_id = fields.Many2one(
        'account.cost.center',
        string='Cost Center',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Default Cost Center',
    )

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        if line.get('cost_center_id'):
            res['cost_center_id'] = line['cost_center_id']
        return res

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()

        for dict_data in res:
            invl_id = dict_data.get('invl_id')
            line = self.env['account.invoice.line'].browse(invl_id)
            if line.cost_center_id:
                dict_data['cost_center_id'] = line.cost_center_id.id

        return res
