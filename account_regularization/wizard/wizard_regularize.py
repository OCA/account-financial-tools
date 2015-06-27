# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields


class WizardRegularize(models.TransientModel):
    _name = 'wizard.regularize'

    @api.model
    def _get_balance_calc(self):
        context = self.env.context
        regularize_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        regularize_id, = regularize_ids
        regul = self.env[active_model].browse(regularize_id)
        return regul.balance_calc

    @api.model
    def _get_fiscalyear(self):
        fiscalyear_obj = self.env['account.fiscalyear']
        return fiscalyear_obj.find()

    @api.model
    def _get_period(self):
        period_obj = self.env['account.period']
        return period_obj.find(dt=fields.Date.today())[0]

    fiscalyear = fields.Many2one('account.fiscalyear', string='Fiscal year',
                                 help='Fiscal Year for the write move',
                                 required=True,
                                 default=_get_fiscalyear)
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 help='Journal for the move',
                                 required=True)
    period_id = fields.Many2one('account.period', string='Period',
                                help='Period for the move',
                                required=True, default=_get_period)
    periods = fields.Many2many('account.period',
                               help='Periods to regularize')
    balance_calc = fields.Selection([('date', 'Date'), ('period', 'Periods')],
                                    'Regularization time calculation',
                                    required=True, visible=False,
                                    default=_get_balance_calc)
    date_move = fields.Date('Date', help='Date for the move',
                            required=True, default=fields.Date.today())
    date_to = fields.Date('Date To',
                          help='Include movements up tho this date',
                          default=fields.Date.today())

    @api.one
    def regularize(self):
        context = self.env.context
        regularize_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        regularize_id, = regularize_ids
        regu = self.env[active_model].browse(regularize_id)
        date = self.date_move
        period = self.period_id
        journal = self.journal_id
        date_to = None
        period_ids = []
        if self.balance_calc == 'date':
            date_to = self.date_to
        if self.balance_calc == 'period':
            period_ids = self.periods
        regu.regularize(date, period, journal, date_to, period_ids)
        return
