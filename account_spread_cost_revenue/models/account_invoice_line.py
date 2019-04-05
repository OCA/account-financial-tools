# Copyright 2016-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    spread_id = fields.Many2one(
        'account.spread',
        string='Spread Board',
        copy=False)
    spread_check = fields.Selection([
        ('linked', 'Linked'),
        ('unlinked', 'Unlinked'),
        ('unavailable', 'Unavailable')
    ], compute='_compute_spread_check')

    @api.depends('spread_id', 'invoice_id.state')
    def _compute_spread_check(self):
        for line in self:
            if line.spread_id:
                line.spread_check = 'linked'
            elif line.invoice_id.state == 'draft':
                line.spread_check = 'unlinked'
            else:
                line.spread_check = 'unavailable'

    @api.multi
    def spread_details(self):
        """Button on the invoice lines tree view of the invoice
        form to show the spread form view."""
        if not self:
            # In case the widget clicked before the creation of the line
            return

        if self.spread_id:
            return {
                'name': _('Spread Details'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.spread',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'readonly': False,
                'res_id': self.spread_id.id,
            }

        # In case no spread board is linked to the invoice line
        # open the wizard to link them
        company = self.invoice_id.company_id
        ctx = dict(
            self.env.context,
            default_invoice_line_id=self.id,
            default_company_id=company.id,
            allow_spread_planning=company.allow_spread_planning,
        )
        return {
            'name': _('Link Invoice Line with Spread Board'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.spread.invoice.line.link.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }
