# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FinancialCancel(models.TransientModel):
    _name = 'financial.cancel'
    _rec_name = 'reason'

    reason = fields.Text(
        string=u'Cancel reason',
        required=True,
        help=u'The reason will be saved in record history',
    )

    def doit(self):
        for wizard in self:
            active_id = self._context['active_id']
            if (self.env.context.get('active_model') == 'financial.move' and
                    active_id):
                fm = self.env['financial.move'].browse(active_id)
                fm.action_cancel(reason=wizard.reason)
        return {
            'type': 'ir.actions.act_window_close',
        }
