# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2004-2011
#     Pexego Sistemas Informáticos. (http://pexego.es)
#     Zikzakmedia S.L. (http://zikzakmedia.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    @api.depends('amount_total', 'amount_untaxed', 'amount_tax',
                 'currency_id', 'move_id')
    def _compute_cc_amount_all(self):
        for inv in self:
            if inv.company_id.currency_id == inv.currency_id:
                inv.cc_amount_untaxed = inv.amount_untaxed
                inv.cc_amount_tax = inv.amount_tax
                inv.cc_amount_total = inv.amount_total
            else:
                inv.cc_amount_untaxed = 0.0
                inv.cc_amount_tax = 0.0
                inv.cc_amount_total = 0.0
                # It could be computed only in open or paid invoices with a
                # generated account move
                if inv.move_id:
                    # Accounts to compute amount_untaxed
                    line_accounts = set([x.account_id.id for x in
                                         inv.invoice_line_ids])
                    # Accounts to compute amount_tax
                    tax_accounts = set([x.account_id.id for x in
                                        inv.tax_line_ids if x.amount != 0])
                    # The company currency amounts are the debit-credit
                    # amounts in the account moves
                    for line in inv.move_id.line_ids:
                        if line.account_id.id in line_accounts:
                            inv.cc_amount_untaxed += line.debit - line.credit
                        if line.account_id.id in tax_accounts:
                            inv.cc_amount_tax += line.debit - line.credit
                    if inv.type in ('out_invoice', 'in_refund'):
                        inv.cc_amount_untaxed = -inv.cc_amount_untaxed
                        inv.cc_amount_tax = -inv.cc_amount_tax
                    inv.cc_amount_total = (inv.cc_amount_tax +
                                           inv.cc_amount_untaxed)

    cc_amount_untaxed = fields.Float(
        compute="_compute_cc_amount_all", digits=dp.get_precision('Account'),
        string='Company Cur. Untaxed',
        help="Invoice untaxed amount in the company currency (useful when "
             "invoice currency is different from company currency).")
    cc_amount_tax = fields.Float(
        compute="_compute_cc_amount_all", digits=dp.get_precision('Account'),
        string='Company Cur. Tax',
        help="Invoice tax amount in the company currency (useful when invoice "
             "currency is different from company currency).")
    cc_amount_total = fields.Float(
        compute="_compute_cc_amount_all", digits=dp.get_precision('Account'),
        string='Company Cur. Total',
        help="Invoice total amount in the company currency (useful when "
             "invoice currency is different from company currency).")
    company_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', readonly=True)
