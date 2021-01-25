# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _


class WizardRebuildMoveAccountInvoice(models.TransientModel):
    _name = "wizard.rebuild.move.account.invoice"

    company_id = fields.Many2one(comodel_name='res.company', string="Company",
                                 default=lambda self: self.env.user.company_id.id)

    @api.multi
    def rebuild_account_invoice(self):
        context = dict(self._context or {})
        invoices = False
        if context.get('active_ids'):
            invoices = self.env['account.invoice'].browse(context["active_ids"])
        if not invoices:
            if self.company_id:
                domain = [('company_id', '=', self.company_id.id)]
            invoices = self.env['account.invoice'].search(domain)
        for invoice in invoices:
            invoice.with_context(self._context, rebuld_try=True).action_invoice_rebuild()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def server_rebuild_action(self):
        for record in self:
            action = self.env.ref('account_recalculate_stock_move.action_recalculate_inventory')
            action.with_context(self._context, company_id=self.env.user.company_id.id, rebuld_try=True).run()
            # _logger.info("ACTION %s" % action)
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def server_rebuild(self):
        if self._context.get('active_ids'):
            company_id = self._context.get('company_id') or self.env.user.company_id.id
            invoices = self.env['account.invoice'].browse(self._context["active_ids"])
            invoices = invoices.filtered(lambda r: r.company_id == company_id)
            invoices.action_invoice_rebuild()
