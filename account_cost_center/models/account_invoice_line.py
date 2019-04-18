# Copyright 2015-2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _default_cost_center(self):
        return self.env['account.cost.center'].browse(
            self.env.context.get('cost_center_id'))

    cost_center_id = fields.Many2one(
        'account.cost.center',
        string='Cost Center',
        index=True,
        default=lambda self: self._default_cost_center(),
    )
