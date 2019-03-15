# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountSpreadContractLineLinkWizard(models.TransientModel):
    _name = 'account.spread.contract.line.link.wizard'
    _description = 'Account Spread Contract Line Link Wizard'

    contract_line_id = fields.Many2one(
        'account.analytic.invoice.line',
        string='Contract Line',
        readonly=True,
        required=True)
    contract_id = fields.Many2one(
        related='contract_line_id.analytic_account_id',
        readonly=True)
    contract_type = fields.Selection(
        related='contract_line_id.analytic_account_id.contract_type',
        readonly=True)
    spread_template_id = fields.Many2one(
        'account.spread.template',
        string='Spread Template',
        required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True)

    @api.multi
    def confirm(self):
        self.ensure_one()

        if not self.contract_line_id.spread_template_id:
            self.contract_line_id.spread_template_id = self.spread_template_id

        if self.spread_template_id:
            return {
                'name': _('Spread Template Details'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.spread.template',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'readonly': False,
                'res_id': self.spread_template_id.id,
            }
