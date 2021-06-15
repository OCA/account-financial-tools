# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    documents_count = fields.Integer(compute="_get_count_documets")

    @api.multi
    def _get_printed_report_name(self, incl=""):
        self.ensure_one()
        name = self.env['account.documents.type'].get_document_type('account.invoice', self.type, self.state)
        if name and "%s" in name:
            return name % incl
        elif name and "%s" not in name:
            return name
        else:
            return _('an unknown name')

    def _get_documents_context(self):
        return "{'default_res_model': '%s','default_res_id': %d}" % ('account.invoice', self.id)

    def _get_documents_domain(self):
        return ['|']

    @api.multi
    def _get_count_documets(self):
        for invoice in self:
            domain = invoice._get_documents_domain()
            if invoice.id and invoice.type in ('in_invoice', 'out_refund'):
                purchase_ids = invoice.invoice_line_ids.mapped('purchase_id')
                domain += ['|',
                    '&', ('res_model', '=', 'account.invoice'), ('res_id', '=', invoice.id),
                    '&', ('res_model', '=', 'purchase.order'), ('res_id', 'in', purchase_ids.ids),
                ]
            elif invoice.id and invoice.type in ('out_invoice', 'in_refund'):
                sale_ids = []
                for line in invoice.invoice_line_ids:
                    for sale_line in line.sale_line_ids:
                        sale_ids.append(sale_line.order_id.id)
                domain += ['|',
                    '&', ('res_model', '=', 'account.invoice'), ('res_id', '=', invoice.id),
                    '&', ('res_model', '=', 'sale.order'), ('res_id', 'in', sale_ids),
                ]
            if invoice.id and invoice.picking_ids:
                domain += [
                    '&', ('res_model', '=', 'stock.picking'), ('res_id', 'in', invoice.picking_ids.ids),
                ]
            else:
                domain = domain[1:]
            invoice.documents_count = self.env['account.documents'].search_count(domain)

    @api.multi
    def action_see_documents(self):
        for invoice in self:
            domain = invoice._get_documents_domain()
            if invoice.id and invoice.type in ('in_invoice', 'out_refund'):
                purchase_ids = invoice.invoice_line_ids.mapped('purchase_id')
                domain += ['|',
                    '&', ('res_model', '=', 'account.invoice'), ('res_id', '=', invoice.id),
                    '&', ('res_model', '=', 'purchase.order'), ('res_id', 'in', purchase_ids.ids),
                    ]
            elif invoice.id and invoice.type in ('out_invoice', 'in_refund'):
                sale_ids = []
                for line in invoice.invoice_line_ids:
                    for sale_line in line.sale_line_ids:
                        sale_ids.append(sale_line.order_id.id)
                domain += ['|',
                    '&', ('res_model', '=', 'account.invoice'), ('res_id', '=', invoice.id),
                    '&', ('res_model', '=', 'sale.order'), ('res_id', 'in', sale_ids),
                    ]
            if invoice.id and invoice.picking_ids:
                domain += [
                    '&', ('res_model', '=', 'stock.picking'), ('res_id', 'in', invoice.picking_ids.ids),
                    ]
            else:
                domain = domain[1:]

            attachment_view = self.env.ref('account_documents.view_documents_file_kanban_account')
            return {
                'name': _('Documents'),
                'domain': domain,
                'res_model': 'account.documents',
                'type': 'ir.actions.act_window',
                'view_id': attachment_view.id,
                'views': [(attachment_view.id, 'kanban'), (False, 'form')],
                'view_mode': 'kanban,tree,form',
                'view_type': 'form',
                'help': _('''<p class="oe_view_nocontent_create">
                            Click to upload document to your invoice.
                        </p><p>
                            Use this feature to store any files, like original invoices.
                        </p>'''),
                'limit': 80,
                'context': invoice._get_documents_context()
                }
        return False


class AccountDocuments(models.Model):
    _inherit = "account.documents"

    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    
    def _get_domain_type(self):
        model_id = self.env['ir.model'].search([('name', '=', 'account.invoice')])
        return super(AccountDocuments, self)._get_domain_type() + [('model_id', '=', model_id.id)]


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def postprocess_pdf_report(self, record, buffer):
        attachment = super(IrActionsReport, self).postprocess_pdf_report(record, buffer)
        if attachment:
            inv = self.env[attachment.res_model].browse(attachment.res_id)
            docs = self.env['account.documents'].search([('ir_attachment_id', '=', attachment.id)])
            if docs and attachment.res_model == 'account.invoice':
                docs.invoice_id = inv
                domain = self.env['account.documents.type']._get_domain('account.invoice', inv.type, inv.state)
                docs.document_type_id = self.env['account.documents.type'].search(domain)
        return attachment
