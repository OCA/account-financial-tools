# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons.queue_job.job import job


class WizardRebuildMoveMrpProduction(models.TransientModel):
    _name = "wizard.rebuild.move.mrp.production"

    company_id = fields.Many2one(comodel_name='res.company', string="Company",
                                 default=lambda self: self.env.user.company_id.id)

    @api.multi
    def rebuild_mrp_production(self):
        self.ensure_one()
        context = dict(self._context or {})
        productions = False
        if context.get('active_ids'):
            productions = self.env['mrp.production'].browse(context["active_ids"])
        if not productions:
            company_id = self.company_id or self.env.user.company_id
            domain = [('company_id', '=', company_id.id)]
            productions = self.env['mrp.production'].search(domain)
        if productions:
            productions.rebuild_account_move()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def server_rebuild_action(self):
        for record in self:
            # action = self.env.ref('account_recalculate_mrp_production.action_recalculate_production')
            # action.with_context(self._context, company_id=self.env.user.company_id.id).run()
            # _logger.info("ACTION %s" % action)
            record.with_delay().server_rebuild()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    @job
    def server_rebuild(self):
        if self._context.get('active_ids'):
            productions = self.env['mrp.production'].browse(self._context["active_ids"])
        else:
            company_id = self.company_id or self.env.user.company_id
            domain = [('company_id', '=', company_id.id)]
            productions = self.env['mrp.production'].search(domain)
        if productions:
            productions.rebuild_account_move()
