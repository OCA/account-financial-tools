# Copyright 2016-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


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

    def create_auto_spread(self):
        """ Create auto spread table for each invoice line, when needed """

        def _filter_line(aline, iline):
            """ Find matching template auto line with invoice line """
            if aline.product_id and iline.product_id != aline.product_id:
                return False
            if aline.account_id and iline.account_id != aline.account_id:
                return False
            if aline.analytic_account_id and \
                    iline.account_analytic_id != aline.analytic_account_id:
                return False
            return True

        for line in self:
            if line.spread_check == 'linked':
                continue
            spread_type = (
                'sale' if line.invoice_type in ['out_invoice', 'out_refund']
                else 'purchase')
            spread_auto = self.env['account.spread.template.auto'].search(
                [('template_id.auto_spread', '=', True),
                 ('template_id.spread_type', '=', spread_type)])
            matched = spread_auto.filtered(lambda a, i=line: _filter_line(a, i))
            template = matched.mapped('template_id')
            if not template:
                continue
            elif len(template) > 1:
                raise UserError(
                    _('Too many auto spread templates (%s) matched with the '
                      'invoice line, %s') % (len(template), line.display_name))
            # Found auto spread template for this invoice line, create it
            wizard = self.env['account.spread.invoice.line.link.wizard'].new({
                'invoice_line_id': line.id,
                'company_id': line.company_id.id,
                'spread_action_type': 'template',
                'template_id': template.id,
            })
            wizard.confirm()
