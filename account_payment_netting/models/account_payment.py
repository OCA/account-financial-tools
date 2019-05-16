# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAbstractPayment(models.AbstractModel):
    _inherit = 'account.abstract.payment'

    netting = fields.Boolean(
        string='Netting',
        help="Technical field, as user select invoice that are both AR and AP",
    )

    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        if not rec.get('multi'):
            return rec
        active_ids = self._context.get('active_ids')
        invoices = self.env['account.invoice'].browse(active_ids)
        types = invoices.mapped('type')
        ap = any(set(['in_invoice', 'in_refund']).intersection(types))
        ar = any(set(['out_invoice', 'out_refund']).intersection(types))
        if ap and ar:  # Both AP and AR -> Netting
            rec.update({'netting': True,
                        'multi': False,  # With netting, allow edit amount
                        'communication': ', '.join(invoices.mapped('number')),
                        })
        return rec

    def _compute_journal_domain_and_types(self):
        if not self.netting:
            return super()._compute_journal_domain_and_types()
        # For case netting, it is possible to have net amount = 0.0
        # without forcing new journal type and payment diff handling
        domain = []
        if self.payment_type == 'inbound':
            domain.append(('at_least_one_inbound', '=', True))
        else:
            domain.append(('at_least_one_outbound', '=', True))
        return {'domain': domain, 'journal_types': set(['bank', 'cash'])}


class AccountRegisterPayments(models.TransientModel):
    _inherit = 'account.register.payments'

    @api.multi
    def get_payments_vals(self):
        """ When doing netting, combine all invoices """
        if self.netting:
            return [self._prepare_payment_vals(self.invoice_ids)]
        return super().get_payments_vals()

    @api.multi
    def _prepare_payment_vals(self, invoices):
        """ When doing netting, partner_type follow payment type """
        values = super()._prepare_payment_vals(invoices)
        if self.netting:
            values['netting'] = self.netting
            values['communication'] = self.communication
            if self.payment_type == 'inbound':
                values['partner_type'] = 'customer'
            elif self.payment_type == 'outbound':
                values['partner_type'] = 'supplier'
        return values

    @api.multi
    def create_payments(self):
        if self.netting:
            self._validate_invoice_netting(self.invoice_ids)
        return super().create_payments()

    @api.model
    def _validate_invoice_netting(self, invoices):
        """ Ensure valid selection of invoice for netting process """
        # All invoice must be of the same partner
        if len(invoices.mapped('commercial_partner_id')) > 1:
            raise UserError(_('All invoices must belong to same partner'))
        # All invoice must have residual
        paid_invoices = invoices.filtered(lambda l: not l.residual)
        if paid_invoices:
            raise UserError(_('Some selected invoices are already paid: %s') %
                            paid_invoices.mapped('number'))


class AccountPayments(models.Model):
    _inherit = 'account.payment'

    @api.one
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        super()._compute_destination_account_id()
        if self.netting:
            if self.partner_type == 'customer':
                self.destination_account_id = \
                    self.partner_id.property_account_receivable_id.id
            else:
                self.destination_account_id = \
                    self.partner_id.property_account_payable_id.id
