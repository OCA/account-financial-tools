# © 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# © 2004-2011 Zikzakmedia S.L. (http://zikzakmedia.com)
#             Jordi Esteve <jesteve@zikzakmedia.com>
# © 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    amount_tax_signed = fields.Monetary(
        string='Tax', currency_field='company_currency_id',
        store=True, readonly=True, compute='_compute_amount',
        help="Invoice tax amount in the company currency, "
             "negative for credit notes.")

    @api.multi
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount',
                 'currency_id', 'company_id')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for inv in self:
            inv.amount_tax_signed = (
                inv.amount_total_company_signed - inv.amount_untaxed_signed)
