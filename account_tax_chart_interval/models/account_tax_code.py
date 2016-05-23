# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import models, fields, api


class AccountTaxCode(models.Model):
    _inherit = 'account.tax.code'

    sum_period = fields.Float(compute="_sum_period")

    @api.one
    def _sum_period(self):
        context = self.env.context
        if context.get('period_ids'):
            move_state = ('posted', )
            if context.get('state', False) == 'all':
                move_state = ('draft', 'posted', )
            self.sum_period = self._sum(
                'sum_period', [],
                where=' AND line.period_id IN %s AND move.state IN %s',
                where_params=(tuple(context['period_ids']),
                              move_state))[self.id]
        else:
            self.sum_period = super(AccountTaxCode,
                                    self)._sum_period('sum_period',
                                                      [])[self.id]
