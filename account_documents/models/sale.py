# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "sale.order"

    documents_count = fields.Integer(compute="_get_count_documets")

    @api.multi
    def _get_printed_report_name(self):
        self.ensure_one()
        name = self.env['account.documents.type'].get_document_type('sale.order', self.type, self.state)
        if name:
            return name
        else:
            return _('an unknown name')

    def _get_documents_context(self):
        return "{'default_res_model': '%s','default_res_id': %d}" % ('sale.order', self.id)

    def _get_documents_domain(self):
        return []

    @api.multi
    def _get_count_documets(self):
        for sale in self:
            domain = sale._get_documents_domain()
            domain += [
                '&', ('res_model', '=', 'sale.order'), ('res_id', '=', sale.id),
                ]
            sale.documents_count = self.env['account.documents'].search_count(domain)

    @api.multi
    def action_see_documents(self):
        for sale in self:
            domain = sale._get_documents_domain()
            domain += [
                '&', ('res_model', '=', 'sale.order'), ('res_id', '=', sale.id),
                ]
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
                            Click to upload document to your Sale Order.
                        </p><p>
                            Use this feature to store any files, like original invoices.
                        </p>'''),
                'limit': 80,
                'context': sale._get_documents_context()
            }
        return False


class AccountDocuments(models.Model):
    _inherit = "account.documents"

    sale_order_id = fields.Many2one('sale.order', 'Sale order')

    def _get_domain_type(self):
        model_id = self.env['ir.model'].search([('name', '=', 'sale.order')])
        return super(AccountDocuments, self)._get_domain_type() + [('model_id', '=', model_id.id)]


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def postprocess_pdf_report(self, record, buffer):
        attachment = super(IrActionsReport, self).postprocess_pdf_report(record, buffer)
        if attachment:
            sale = self.env[attachment.res_model].browse(attachment.res_id)
            docs = self.env['account.documents'].search([('ir_attachment_id', '=', attachment.id)])
            if docs and attachment.res_model == 'sale.order':
                docs.sale_order_id = sale
                domain = self.env['account.documents.type']._get_domain('sale.order', '', sale.state)
                docs.document_type_id = self.env['account.documents.type'].search(domain)
        return attachment
