# -*- coding: utf-8 -*-
# Copyright 2017 PRAXYA (<http://praxya.com/>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.onchange('date')
    def _onchange_move_date(self):
        if self.date:
            period_obj = self.env['account.period']
            period_id = period_obj.find(self.date)
            self.period_id = period_id
            return period_id
        return False
