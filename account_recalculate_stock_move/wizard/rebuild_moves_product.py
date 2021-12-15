# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import uuid

from odoo import models, fields, api, _
# from odoo.addons.queue_job.job import job


class WizardRebuildMovesProducts(models.TransientModel):
    _name = "wizard.rebuild.moves.products"

    company_id = fields.Many2one(comodel_name='res.company', string="Company",
                                 default=lambda self: self.env.user.company_id.id)

    @api.multi
    def rebuild_moves_server(self):
        context = dict(self._context or {})
        products = False
        if context.get('active_ids'):
            products = self.env['product.template'].browse(context["active_ids"])
        if not products:
            return {'type': 'ir.actions.act_window_close'}
        # batch = self.env['queue.job.batch'].get_new_batch('Product template %s' % str(uuid.uuid4()))
        # for product in products:
        products.with_delay().server_rebuild_action()
        # batch.enqueue()
        return {'type': 'ir.actions.act_window_close'}
