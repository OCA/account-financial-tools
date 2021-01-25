# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)

class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    documents_count = fields.Integer(compute="_get_count_documets")

    def _get_documents_context(self):
        return "{'default_res_model': '%s','default_res_id': %d}" % ('account.bank.statement', self.id)

    def _get_documents_domain(self):
        return []

    @api.multi
    def _get_count_documets(self):
        for picking in self:
            domain = picking._get_documents_domain()
            domain += [
                '&', ('res_model', '=', 'account.bank.statement'), ('res_id', '=', picking.id),
            ]
            picking.documents_count = self.env['account.documents'].search_count(domain)

    @api.multi
    def action_see_documents(self):
        for bank in self:
            domain = bank._get_documents_domain()
            domain += [
                '&', ('res_model', '=', 'account.bank.statement'), ('res_id', '=', bank.id),
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
                'context': bank._get_documents_context()
            }
        return False
