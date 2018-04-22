# Copyright 2011- Slobodni programi d.o.o.
# Copyright 2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

# Update type refund in storno
TYPE2REFUND = {
    'out_invoice': 'out_invoice',      # Customer Invoice
    'in_invoice': 'in_invoice',        # Vendor Bill
    'out_refund': 'out_refund',        # Customer Credit Note
    'in_refund': 'in_refund',          # Vendor Credit Note
}
TYPE2ACTION = {
    'out_invoice': 'action_invoice_tree1',        # Customer Invoice
    'in_invoice': 'action_invoice_tree2',         # Vendor Bill
    'out_refund': 'action_invoice_out_refund',    # Customer Credit Note
    'in_refund': 'action_invoice_in_refund',      # Vendor Credit Note
}


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    filter_refund = fields.Selection(
        selection_add=[('storno', 'Create a storno invoice.')])

    @api.multi
    def compute_refund(self, mode='refund'):
        inv_obj = self.env['account.invoice']
        context = dict(self._context or {})
        xml_id = False

        if mode == 'storno':
            for form in self:
                created_inv = []
                date = False
                description = False
                for inv in inv_obj.browse(context.get('active_ids')):
                    if inv.state in ['draft', 'cancel']:
                        raise UserError(_('Cannot create credit note for the '
                                          'draft/cancelled invoice.'))
                    if inv.reconciled and mode in ('cancel', 'modify'):
                        raise UserError(
                            _('Cannot create credit note for the invoice which'
                              ' is already reconciled. The invoice should be'
                              ' unreconciled first: only then can you add'
                              ' credit note for this invoice.'))

                    date = form.date or False
                    description = form.description or inv.name
                    refund = inv.refund(form.date_invoice, date,
                                        description, inv.journal_id.id)

                    refund.type = TYPE2REFUND[inv.type]
                    created_inv.append(refund.id)
                    for inv_line in refund.invoice_line_ids:
                        inv_line.quantity = -inv_line.quantity
                    xml_id = TYPE2ACTION[inv.type]
                    # Put the reason in the chatter
                    subject = _("Storno Invoice")
                    body = description
                    refund.message_post(body=body, subject=subject)
                    refund.compute_taxes()
            if xml_id:
                result = self.env.ref('account.%s' % (xml_id)).read()[0]
                invoice_domain = safe_eval(result['domain'])
                invoice_domain.append(('id', 'in', created_inv))
                result['domain'] = invoice_domain
                return result
        return super(AccountInvoiceRefund, self).compute_refund(mode)
