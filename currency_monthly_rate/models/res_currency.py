# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class ResCurrency(models.Model):
    _inherit = "res.currency"

    monthly_rate = fields.Float(compute='_compute_current_monthly_rate',
                                string='Current Monthly Rate', digits=(12, 6),
                                help='The monthly rate of the currency to '
                                     'the currency of rate 1.')
    monthly_rate_ids = fields.One2many('res.currency.rate.monthly',
                                       'currency_id', string='Monthly rates')

    @api.multi
    def _compute_current_monthly_rate(self):
        date = self.env.context.get('date') or fields.Date.today()
        company_id = self.env.context.get('company_id') or self.env[
            'res.users']._get_company().id
        # the subquery selects the first rate before 'date' for the given
        # currency/company
        query = """SELECT c.id, (SELECT r.rate
                                 FROM res_currency_rate_monthly r
                                 WHERE r.currency_id = c.id
                                 AND r.name <= %s
                                 AND (r.company_id IS NULL
                                      OR r.company_id = %s)
                                 ORDER BY r.company_id, r.name DESC
                                 LIMIT 1) AS rate
                   FROM res_currency c
                   WHERE c.id IN %s"""
        self._cr.execute(query, (date, company_id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())
        for currency in self:
            currency.monthly_rate = currency_rates.get(currency.id) or 1.0

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency):
        monthly = self.env.context.get('monthly_rate')
        if not monthly:
            return super()._get_conversion_rate(from_currency, to_currency)
        from_currency = from_currency.with_env(self.env)
        to_currency = to_currency.with_env(self.env)
        return to_currency.monthly_rate / from_currency.monthly_rate


class ResCurrencyRateMonthly(models.Model):

    _inherit = "res.currency.rate"
    _name = "res.currency.rate.monthly"
    _description = "Currency monthly rate"

    def _default_get_month(self):
        return fields.Date.from_string(
            fields.Date.context_today(self)).strftime('%m')

    def _default_get_year(self):
        return fields.Date.from_string(
            fields.Date.context_today(self)).strftime('%Y')

    name = fields.Date(compute='_compute_name', store=True, required=True,
                       index=True)
    year = fields.Char(size=4, required=True,
                       default=lambda self: self._default_get_year())
    month = fields.Selection([('01', 'January'),
                              ('02', 'February'),
                              ('03', 'March'),
                              ('04', 'April'),
                              ('05', 'May'),
                              ('06', 'June'),
                              ('07', 'July'),
                              ('08', 'August'),
                              ('09', 'September'),
                              ('10', 'October'),
                              ('11', 'November'),
                              ('12', 'December')], required=True,
                             default=lambda self: self._default_get_month())

    @api.depends('year', 'month')
    def _compute_name(self):
        for rate in self:
            rate.name = fields.Date.from_string('%s-%s-01' % (
                rate.year, rate.month))

    # The two constraints have the same message because, the first is a
    # redefinition of the constraint inherited from res.currency.rate and
    # the second makes it stronger
    _sql_constraints = [
        ('unique_name_per_day', 'unique (name,currency_id,company_id)',
         _('Only one currency monthly rate per month allowed!')),
        ('unique_year_month', 'unique (year,month,currency_id,company_id)',
         _('Only one currency monthly rate per month allowed!'))
    ]
