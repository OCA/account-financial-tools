# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class FinancialCancel(models.TransientModel):
    _name = 'financial.cancel'

    motivo_cancelamento_id = fields.Many2one(
        comodel_name="financial.move.motivo.cancelamento",
        string="Motivo do Cancelamento",
        required=True,
    )

    obs = fields.Text(
        string=u'Observações',
    )

    @api.multi
    def doit(self):
        for wizard in self:
            active_id = self._context['active_id']
            if (self.env.context.get('active_model') == 'financial.move' and
                    active_id):
                fm = self.env['financial.move'].browse(active_id)
                fm.action_cancel(
                    motivo_id=wizard.motivo_cancelamento_id.id, obs=wizard.obs
                )
        return {
            'type': 'ir.actions.act_window_close',
        }
