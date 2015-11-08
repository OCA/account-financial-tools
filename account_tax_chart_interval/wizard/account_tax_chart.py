# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

from openerp import models, fields, api


class AccountTaxChart(models.TransientModel):
    _inherit = 'account.tax.chart'

    def default_fiscalyear(self):
        return self.env['account.fiscalyear'].find()

    fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear', string='Fiscal year',
        default=default_fiscalyear)
    period_from = fields.Many2one(
        comodel_name='account.period', string='Start period',
        domain="[('fiscalyear_id', '=', fiscalyear_id)]")
    period_to = fields.Many2one(
        comodel_name='account.period', string='End period',
        domain="[('fiscalyear_id', '=', fiscalyear_id)]")

    @api.one
    @api.onchange('fiscalyear_id')
    def onchange_fiscalyear(self):
        self.period_from = (self.fiscalyear_id.period_ids and
                            self.fiscalyear_id.period_ids[0] or False)
        self.period_to = (self.fiscalyear_id.period_ids and
                          self.fiscalyear_id.period_ids[-1] or False)

    @api.multi
    def account_tax_chart_open_window(self):
        res = super(AccountTaxChart, self).account_tax_chart_open_window()
        res['context'] = eval(res['context'])
        if self.fiscalyear_id:
            res['context']['fiscalyear_id'] = self.fiscalyear_id.id
        if self.period_from and self.period_to:
            res['context']['period_ids'] = (
                self.env['account.period'].build_ctx_periods(
                    self.period_from.id, self.period_to.id))
            name = res['name']
            if name.find(':'):
                name = name[:name.find(':')]
            name += ":%s-%s" % (self.period_from.code, self.period_to.code)
            res['name'] = name
        return res
