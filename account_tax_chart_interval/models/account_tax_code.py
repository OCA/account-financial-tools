# -*- coding: utf-8 -*-
# Copyright 2015 Serv. Tecnol. Avanzados <http://www.serviciosbaeza.com>
# Copyright 2015 Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api


class AccountTaxCode(models.Model):
    _inherit = 'account.tax.code'

    sum_period = fields.Float(compute="_compute_sum_period")

    @api.multi
    def _compute_sum_period(self):
        for rec in self:
            if self.env.context.get('period_ids'):
                move_state = ('posted', )
                if self.env.context.get('state') == 'all':
                    move_state = ('draft', 'posted', )
                rec.sum_period = rec._sum(
                    'sum_period', [],
                    where=' AND line.period_id IN %s AND move.state IN %s',
                    where_params=(
                        tuple(self.env.context.get('period_ids')),
                        move_state))[rec.id]
            else:
                rec.sum_period = super(AccountTaxCode, self) \
                    ._compute_sum_period()
