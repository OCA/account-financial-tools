# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FinancialRenegociate(models.TransientModel):

    _name = 'financial.renegociate'

    name = fields.Char()

    @api.multi
    def doit(self):
        result_ids = []
        for wizard in self:
            # TODO
            pass
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Action Name',  # TODO
            'res_model': 'result.model',  # TODO
            'domain': [('id', '=', result_ids)],  # TODO
            'view_mode': 'form,tree',
        }
        return action
