# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    @api.multi
    def _create_invoice(self, invoice=False):
        """
        :param invoice: If not False add lines to this invoice
        :return: invoice created or updated
        """
        self.ensure_one()

        line_template_map = {}
        for line in self.recurring_invoice_line_ids:
            if invoice and invoice.state == 'draft':
                pass
            else:
                self._create_spread_by_template_map(line, line_template_map)
        ctx = dict(
            self.env.context,
            contract_spread_template_map=line_template_map,
        )
        res = super(
            AccountAnalyticAccount,
            self.with_context(ctx)
        )._create_invoice(invoice)
        for line in self.recurring_invoice_line_ids:
            if line.id in line_template_map:
                spread_id = line_template_map[line.id]
                spread = self.env['account.spread'].browse(spread_id)
                spread.compute_spread_board()
        return res

    def _create_spread_by_template_map(self, line, line_template_map):
        self.ensure_one()
        if line.spread_template_id:
            new_spread_vals = self._prepare_spread_vals(line)
            new_spread = self.env['account.spread'].create(new_spread_vals)
            line_template_map[line.id] = new_spread.id

    def _prepare_spread_vals(self, line):
        self.ensure_one()
        template = line.spread_template_id
        new_spread_vals = template._prepare_spread_from_template()
        invoice_type = 'out_invoice'
        if self.contract_type == 'purchase':
            invoice_type = 'in_invoice'

        fpos_id = self._prepare_invoice().get('fiscal_position_id')
        fiscal_position = self.env['account.fiscal.position'].browse(fpos_id)
        account = self.env['account.invoice.line'].get_invoice_line_account(
            invoice_type,
            line.product_id,
            fiscal_position,
            self.company_id
        )
        if not account:
            raise UserError(_("Unable to get the Invoice Line Account."))

        if self.contract_type == 'purchase':
            new_spread_vals['debit_account_id'] = account.id
        else:
            new_spread_vals['credit_account_id'] = account.id

        lang = self.env['res.lang'].search(
            [('code', '=', self.partner_id.lang)])
        date_format = lang.date_format or '%m/%d/%Y'
        invoice_line_name = self._insert_markers(line, date_format)
        spread_name = _('Contract %s (%s) %s') % (
            self.name,
            self.recurring_next_date,
            invoice_line_name
        )
        analytic_tags = [(4, tag.id, None) for tag in self.tag_ids]

        new_spread_vals.update({
            'name': spread_name,
            'period_number': self.recurring_interval,
            'period_type': self._get_spread_period_type(),
            'spread_date': self.recurring_next_date,
            'account_analytic_id': self.id,
            'analytic_tag_ids': analytic_tags,
        })
        return new_spread_vals

    def _get_spread_period_type(self):
        self.ensure_one()
        recurring_rule_type = self.recurring_rule_type
        if recurring_rule_type not in ['monthly', 'monthlylastday', 'yearly']:
            raise UserError(
                _("Not implemented."))

        if recurring_rule_type == 'yearly':
            return 'year'
        return 'month'

    @api.model
    def _prepare_invoice_line(self, line, invoice_id):
        template_map = self.env.context.get('contract_spread_template_map')
        res = super()._prepare_invoice_line(line, invoice_id)
        if line.id in template_map:
            spread_id = template_map[line.id]
            res['spread_id'] = spread_id
        return res
