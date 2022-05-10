# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import uuid

from odoo import models, fields, api, _
# from odoo.addons.queue_job.job import job


class WizardClearReservationProducts(models.TransientModel):
    _name = "wizard.clear.reservation.products"

    company_id = fields.Many2one(comodel_name='res.company', string="Company",
                                 default=lambda self: self.env.user.company_id.id)

    @api.multi
    def clear_reservation_server(self):
        context = dict(self._context or {})
        products = False
        if context.get('active_ids'):
            products = self.env['product.template'].browse(context["active_ids"])
        if not products:
            return {'type': 'ir.actions.act_window_close'}
        products.with_delay().server_clear_reservation_action()
        return {'type': 'ir.actions.act_window_close'}
