# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Picking(models.Model):
    _inherit = "stock.picking"

    documents_count = fields.Integer(compute="_get_count_documets")

    def _get_documents_context(self):
        return "{'default_res_model': '%s','default_res_id': %d}" % ('stock.picking', self.id)

    def _get_documents_domain(self):
        return []

    @api.multi
    def _get_count_documets(self):
        for picking in self:
            domain = picking._get_documents_domain()
            domain += [
                '&', ('res_model', '=', 'stock.picking'), ('res_id', '=', picking.id),
                ]
            picking.documents_count = self.env['account.documents'].search_count(domain)

    @api.multi
    def action_see_documents(self):
        for picking in self:
            domain = picking._get_documents_domain()
            domain += [
                '&', ('res_model', '=', 'stock.picking'), ('res_id', '=', picking.id),
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
                            Click to upload document to your Picking.
                        </p><p>
                            Use this feature to store any files, like original invoices.
                        </p>'''),
                'limit': 80,
                'context': picking._get_documents_context()
            }
        return False


class AccountDocuments(models.Model):
    _inherit = "account.documents"

    stock_picking_id = fields.Many2one('stock.picking', 'Stock picking')

    def _get_domain_type(self):
        model_id = self.env['ir.model'].search([('name', '=', 'stock.picking')])
        return super(AccountDocuments, self)._get_domain_type() + [('model_id', '=', model_id.id)]


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.multi
    def postprocess_pdf_report(self, record, buffer):
        attachment = super(IrActionsReport, self).postprocess_pdf_report(record, buffer)
        if attachment:
            picking = self.env[attachment.res_model].browse(attachment.res_id)
            docs = self.env['account.documents'].search([('ir_attachment_id', '=', attachment.id)])
            if docs and attachment.res_model == 'stock.picking':
                docs.stock_picking_id = picking
                domain = self.env['account.documents.type']._get_domain('stock.picking', picking.picking_type_code, picking.state)
                docs.document_type_id = self.env['account.documents.type'].search(domain)
        return attachment
