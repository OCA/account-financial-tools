# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.account.models import account_move as AccountMove


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_base = fields.Monetary(default=0.0, currency_field='company_currency_id')

    @api.multi
    def _prepare_writeoff_first_line_values(self, values):
        line_values = values.copy()
        line_values['account_id'] = self[0].account_id.id
        if 'analytic_account_id' in line_values:
            del line_values['analytic_account_id']
        if 'tax_ids' in line_values:
            tax_ids = []
            # vals['tax_ids'] is a list of commands [[4, tax_id, None], ...]
            for tax_id in values['tax_ids']:
                tax_ids.append(tax_id[1])
            taxes = self.env['account.tax'].browse(tax_ids)
            sale = any([tax.type_tax_use == 'sales' for tax in taxes])
            # Check second possibility in child taxes
            purchase = any([tax.type_tax_use == 'purchase' for tax in taxes])
            # Check second possibility in child taxes
            amount = line_values['credit'] - line_values['debit']
            amount_tax = taxes.compute_all(amount)['total_included']
            line_values['credit'] = amount_tax > 0 and amount_tax or 0.0
            line_values['debit'] = amount_tax < 0 and abs(amount_tax) or 0.0
            line_values['tax_base'] = amount
            if sale and line_values['debit'] > 0.0:
                line_values['tax_sign'] = -1
            if purchase and line_values['credit'] > 0.0:
                line_values['tax_sign'] = -1
            del line_values['tax_ids']
        return line_values

    def _get_taxes_values(self, tax, tax_type_deal):
        if tax.tax_type_deal and tax.tax_type_deal != tax_type_deal:
            return True
        return False

    def _apply_taxes(self, vals, amount):
        tax_lines_vals = []
        # Get ids from triplets : https://www.odoo.com/documentation/10.0/reference/orm.html#odoo.models.Model.write
        tax_ids = [tax['id'] for tax in self.resolve_2many_commands('tax_ids', vals['tax_ids']) if tax.get('id')]
        # Since create() receives ids instead of recordset, let's just use the old-api bridge
        taxes = self.env['account.tax'].browse(tax_ids)
        currency = self.env['res.currency'].browse(vals.get('currency_id'))
        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        ctx = dict(self._context)
        ctx['round'] = ctx.get('round', True)
        res = taxes.with_context(ctx).compute_all(amount,
            currency, 1, vals.get('product_id'), partner)
        # Adjust line amount if any tax is price_include
        if abs(res['total_excluded']) < abs(amount):
            if vals['debit'] != 0.0: vals['debit'] = res['total_excluded']
            if vals['credit'] != 0.0: vals['credit'] = -res['total_excluded']
            if vals.get('amount_currency'):
                vals['amount_currency'] = self.env['res.currency'].browse(vals['currency_id']).round(vals['amount_currency'] * (res['total_excluded']/amount))
        # Create tax lines
        for tax_vals in res['taxes']:
            if tax_vals['amount']:
                tax = self.env['account.tax'].browse([tax_vals['id']])
                if 'tax_type_deal' in tax._fields and 'tax_type_deal' in self._fields and self._get_taxes_values(tax, self.tax_type_deal):
                    continue
                sale = tax.type_tax_use == 'sale'
                purchase = tax.type_tax_use == 'purchase'
                account_id = (amount > 0 and tax_vals['account_id'] or tax_vals['refund_account_id'])
                if not account_id: account_id = vals['account_id']
                temp = {
                    'account_id': account_id,
                    'name': vals['name'] + ' ' + tax_vals['name'],
                    'tax_line_id': tax_vals['id'],
                    'move_id': vals['move_id'],
                    'partner_id': vals.get('partner_id'),
                    'statement_id': vals.get('statement_id'),
                    'tax_base': amount,
                    'tax_sign': ((sale and tax_vals['amount'] > 0) or (purchase and tax_vals['amount'] < 0)) and -1 or 1,
                    'debit': tax_vals['amount'] > 0 and tax_vals['amount'] or 0.0,
                    'credit': tax_vals['amount'] < 0 and -tax_vals['amount'] or 0.0,
                    'analytic_account_id': vals.get('analytic_account_id') if tax.analytic else False,
                }
                bank = self.env["account.bank.statement.line"].browse(vals.get('statement_line_id')).statement_id
                if bank and bank.currency_id != bank.company_id.currency_id:
                    ctx = {}
                    if 'date' in vals:
                        ctx['date'] = vals['date']
                    elif 'date_maturity' in vals:
                        ctx['date'] = vals['date_maturity']
                    temp['currency_id'] = bank.currency_id.id
                    temp['amount_currency'] = bank.company_id.currency_id.with_context(ctx).compute(tax_vals['amount'], bank.currency_id, round=True)
                if vals.get('tax_exigible'):
                    temp['tax_exigible'] = True
                    temp['account_id'] = tax.cash_basis_account.id or account_id
                tax_lines_vals.append(temp)
                if tax and \
                        tax.tax_credit_payable in ['taxadvpay', 'eutaxpay', 'eutaxcredit'] and \
                        tax.separate and \
                        tax.contrapart_account_id:
                    tax_lines_vals[-1]['separate'] = -1
                    contrapart_line = tax_lines_vals[-1].copy()

                    contrapart_line['debit'] = tax_vals['amount'] < 0 and tax_vals['amount'] or 0.0
                    contrapart_line['credit'] = tax_vals['amount'] > 0 and -tax_vals['amount'] or 0.0
                    contrapart_line['account_id'] = tax.contrapart_account_id.id
                    contrapart_line['name'] = _("Contrapart for %s" % contrapart_line['name'])
                    contrapart_line['separate'] = 1
                    tax_lines_vals.append(contrapart_line)
        return tax_lines_vals

AccountMove.AccountMoveLine._apply_taxes = AccountMoveLine._apply_taxes
AccountMove.AccountMoveLine._prepare_writeoff_first_line_values = AccountMoveLine._prepare_writeoff_first_line_values
