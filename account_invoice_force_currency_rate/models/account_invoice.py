# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
#                      Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    currency_rate = fields.Many2one(
        'res.currency.rate',
        'Currency Rate',
        default=False)

    @api.onchange('currency_id', 'date_invoice')
    def change_currency_id(self):
        rate_domain = [
            ('currency_id', '=', self.currency_id.id)
        ]
        if self.date_invoice:
            rate_domain.append(('name', '<=', self.date_invoice))
        rates = self.env['res.currency.rate'].search(rate_domain,
                                                     order="name desc")
        self.currency_rate = rates and rates[0]

    def compute_invoice_totals(self, company_currency, ref,
                               invoice_move_lines):
        initial_invoice_move_lines = list(invoice_move_lines)
        if self.type in ('in_invoice') and \
                self.currency_id != company_currency:
            total = 0
            total_currency = 0
            for line in invoice_move_lines:
                currency = self.currency_id.with_context(
                    date=self.currency_rate.name or
                    fields.Date.context_today(self))
                line['currency_id'] = currency.id
                line['amount_currency'] = currency.round(line['price'])
                line['price'] = currency.compute(
                    line['price'], company_currency)
                line['ref'] = ref

                total -= line['price']
                total_currency -= line['amount_currency'] or line['price']
            return total, total_currency, invoice_move_lines
        return super(AccountInvoice, self).compute_invoice_totals(
            company_currency, ref, initial_invoice_move_lines)
