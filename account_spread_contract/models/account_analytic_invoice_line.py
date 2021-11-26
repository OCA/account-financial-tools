# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountAnalyticInvoiceLine(models.Model):
    _inherit = 'account.analytic.invoice.line'

    spread_template_id = fields.Many2one(
        'account.spread.template',
        string='Spread Template',
        copy=False)
    spread_check = fields.Selection([
        ('linked', 'Linked'),
        ('unlinked', 'Unlinked'),
        ('unavailable', 'Unavailable')
    ], compute='_compute_spread_check')

    @api.depends('spread_template_id')
    def _compute_spread_check(self):
        for line in self:
            if line.spread_template_id:
                line.spread_check = 'linked'
            elif not line.analytic_account_id.create_invoice_visibility:
                line.spread_check = 'unavailable'
            else:
                line.spread_check = 'unlinked'

    @api.multi
    def spread_details(self):
        """Button on the contract lines tree view of the contract
        form to show the spread template form view."""
        if not self:
            # In case the widget clicked before the creation of the line
            return

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
                'context': {'force_contract_line_id': self.id},
            }

        ctx = dict(
            self.env.context,
            default_contract_line_id=self.id,
            default_company_id=self.analytic_account_id.company_id.id,
        )
        return {
            'name': _('Link Contract Line with Spread Template'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.spread.contract.line.link.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }
