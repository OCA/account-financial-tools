# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.addons.account.models import account_invoice as accountinvoice

import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    tag_ids = fields.Many2many(related='tax_id.tag_ids', string='Tags', help="Optional tags you may want to assign for custom reporting")


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        account_id = False
        payment_term_id = False
        fiscal_position = False
        bank_id = False
        warning = {}
        domain = {}
        company_id = self.company_id.id
        p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
        type = self.type
        if p:
            rec_account = p.property_account_receivable_id
            pay_account = p.property_account_payable_id
            if not rec_account and not pay_account:
                action = self.env.ref('account.action_account_config')
                msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            if type in ('in_invoice', 'in_refund'):
                account_id = pay_account.id
                payment_term_id = p.property_supplier_payment_term_id.id
            else:
                account_id = rec_account.id
                payment_term_id = p.property_payment_term_id.id

            delivery_partner_id = self.get_delivery_partner_id()
            fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, delivery_id=delivery_partner_id)
            fp = self.env['account.fiscal.position'].browse(fiscal_position)

            if fp:
                fp_account_id = self.env['account.account'].browse(account_id)
                fp_account_id = fp.map_account(fp_account_id)
                if fp_account_id:
                    account_id = fp_account_id

            # If partner has no warning, check its company
            if p.invoice_warn == 'no-message' and p.parent_id:
                p = p.parent_id
            if p.invoice_warn != 'no-message':
                # Block if partner only has warning but parent company is blocked
                if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
                    p = p.parent_id
                warning = {
                    'title': _("Warning for %s") % p.name,
                    'message': p.invoice_warn_msg
                    }
                if p.invoice_warn == 'block':
                    self.partner_id = False

        self.account_id = account_id
        self.payment_term_id = payment_term_id
        self.date_due = False
        self.fiscal_position_id = fiscal_position

        if type in ('in_invoice', 'out_refund'):
            bank_ids = p.commercial_partner_id.bank_ids
            bank_id = bank_ids[0].id if bank_ids else False
            self.partner_bank_id = bank_id
            domain = {'partner_bank_id': [('id', 'in', bank_ids.ids)]}

        res = {}
        if warning:
            res['warning'] = warning
        if domain:
            res['domain'] = domain
        return res

accountinvoice.AccountInvoice._onchange_partner_id = AccountInvoice._onchange_partner_id
