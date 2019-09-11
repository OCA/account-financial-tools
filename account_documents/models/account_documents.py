# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
#from odoo.addons.account.models.account_invoice import TYPE2REFUND

import logging
_logger = logging.getLogger(__name__)


class AccountDocuments(models.Model):
    _name = "account.documents"
    _description = "Collection of all scaned and copy of original documents linked with deal."
    _inherits = {'ir.attachment': 'ir_attachment_id',}

    def _get_domain_type(self):
        return [('display', '=', True)]

    ir_attachment_id = fields.Many2one('ir.attachment', string='Related attachment', required=True, ondelete='cascade')
    document_type_id = fields.Many2one('account.documents.type', 'Type of document', domain=_get_domain_type)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def postprocess_pdf_report(self, record, buffer):
        attachment = super(IrActionsReport, self).postprocess_pdf_report(record, buffer)
        if attachment:
            docs = self.env['account.documents'].search([('ir_attachment_id', '=', attachment.id)])
            if not docs:
                docs.create({'ir_attachment_id': attachment.id})
        return attachment


class AccountDocumentsType(models.Model):
    _name = "account.documents.type"
    _description = "Global nomeclature for parce documents."

    active = fields.Boolean('Active', default=True,
            help="If the active field is set to False, it will allow you to hide the Type documents without removing it.")
    model_id = fields.Many2one('ir.model', string='Odoo model')
    type = fields.Char('Type')
    state = fields.Char('State')
    print_name = fields.Char('Print name', translate=True)
    name = fields.Char('Name', translate=True)

    display = fields.Boolean()

    def _get_domain(self, model, type, state):
        model_id = self.env['ir.model'].search([('name', '=', model)])
        domain = [('model_id', '=', model_id.id), ('type', '=', type), ('state', '=', state)]
        return domain

    def get_document_type(self, model, type, state, field_name='print_name'):
        type = self.search(self._get_domain(model, type, state))
        return getattr(type, field_name)

        #return self.type == 'out_invoice' and self.state == 'draft' and _('Draft Invoice') or \
        #       self.type == 'out_invoice' and self.state in ('open', 'paid') and _('Invoice - %s') % (self.number) or \
        #       self.type == 'out_refund' and self.state == 'draft' and _('Credit Note') or \
        #       self.type == 'out_refund' and _('Credit Note - %s') % (self.number) or \
        #       self.type == 'in_invoice' and self.state == 'draft' and _('Vendor Bill') or \
        #       self.type == 'in_invoice' and self.state in ('open', 'paid') and _('Vendor Bill - %s') % (self.number) or \
        #       self.type == 'in_refund' and self.state == 'draft' and _('Vendor Credit Note') or \
        #       self.type == 'in_refund' and _('Vendor Credit Note - %s') % (self.number)
