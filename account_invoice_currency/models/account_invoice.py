# -*- coding: utf-8 -*-
# © 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# © 2004-2011 Zikzakmedia S.L. (http://zikzakmedia.com)
#             Jordi Esteve <jesteve@zikzakmedia.com>
# © 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Antiun Ingenieria S.L. - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.depends('amount_total', 'amount_untaxed', 'amount_tax',
                 'currency_id', 'move_id')
    def _cc_amount_all(self):
        for invoice in self:
            if invoice.company_id.currency_id == invoice.currency_id:
                invoice.cc_amount_untaxed = invoice.amount_untaxed
                invoice.cc_amount_tax = invoice.amount_tax
                invoice.cc_amount_total = invoice.amount_total
            else:
                invoice.cc_amount_untaxed = 0.0
                invoice.cc_amount_tax = 0.0
                invoice.cc_amount_total = 0.0
                # It could be computed only in open or paid invoices with a
                # generated account move
                if invoice.move_id:
                    # Accounts to compute amount_untaxed
                    line_accounts = set([x.account_id.id for x in
                                         invoice.invoice_line])
                    # Accounts to compute amount_tax
                    tax_accounts = set([x.account_id.id for x in
                                        invoice.tax_line if x.amount != 0])
                    # The company currency amounts are the debit-credit
                    # amounts in the account moves
                    for line in invoice.move_id.line_id:
                        if line.account_id.id in line_accounts:
                            invoice.cc_amount_untaxed += (
                                line.debit - line.credit)
                        if line.account_id.id in tax_accounts:
                            invoice.cc_amount_tax += line.debit - line.credit
                    if invoice.type in ('out_invoice', 'in_refund'):
                        invoice.cc_amount_untaxed = -invoice.cc_amount_untaxed
                        invoice.cc_amount_tax = -invoice.cc_amount_tax
                    invoice.cc_amount_total = (invoice.cc_amount_tax +
                                               invoice.cc_amount_untaxed)

    cc_amount_untaxed = fields.Float(
        compute="_cc_amount_all", digits=dp.get_precision('Account'),
        string='Company Cur. Untaxed', store=True, readonly=True,
        help="Invoice untaxed amount in the company currency (useful when "
             "invoice currency is different from company currency).")
    cc_amount_tax = fields.Float(
        compute="_cc_amount_all", digits=dp.get_precision('Account'),
        string='Company Cur. Tax', store=True, readonly=True,
        help="Invoice tax amount in the company currency (useful when invoice "
             "currency is different from company currency).")
    cc_amount_total = fields.Float(
        compute="_cc_amount_all", digits=dp.get_precision('Account'),
        string='Company Cur. Total', store=True, readonly=True,
        help="Invoice total amount in the company currency (useful when "
             "invoice currency is different from company currency).")
