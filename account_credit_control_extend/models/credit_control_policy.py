# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class CreditControlPolicy(models.Model):
    _inherit = "credit.control.policy"

    @api.multi
    def _move_lines_domain(self, controlling_date):
        default_partner_id = self._context.get('default_partner_id', False)
        res = super(CreditControlPolicy, self)._move_lines_domain(controlling_date)
        if not default_partner_id:
            return res
        for i, x in enumerate(res):
            if x[0] == 'partner_id':
                res[i] = ('partner_id', '=', default_partner_id)
        return res
