# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountSpreadTemplate(models.Model):
    _inherit = 'account.spread.template'

    contract_line_ids = fields.One2many(
        'account.analytic.invoice.line',
        'spread_template_id',
        string='Contract Lines',
    )

    @api.constrains('contract_line_ids', 'spread_type')
    def _check_spread_template_contract_type(self):
        for template in self:
            for line in template.contract_line_ids:
                contract = line.analytic_account_id.contract_template_id
                contract_type = contract.contract_type
                if contract_type == 'sale' or not contract_type:
                    if template.spread_type != 'sale':
                        raise ValidationError(_(
                            'The contract type (Sales) is not compatible '
                            'with selected Template Spread Type'))
                elif contract_type == 'purchase':
                    if template.spread_type != 'purchase':
                        raise ValidationError(_(
                            'The contract type (Purchases) is not compatible '
                            'with selected Template Spread Type'))

    @api.multi
    def action_unlink_contract_line(self):
        line_id = self.env.context.get('force_contract_line_id')
        line = self.env['account.analytic.invoice.line'].browse(line_id)
        line.spread_template_id = False
