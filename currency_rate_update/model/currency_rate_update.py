# -*- coding: utf-8 -*-
# © 2009-2016 Camptocamp
# © 2010 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from openerp import models, fields, api, _
from openerp import exceptions

from ..services.currency_getter_interface import CurrencyGetterType


_logger = logging.getLogger(__name__)

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
}


class CurrencyRateUpdateService(models.Model):
    """Class keep services and currencies that
    have to be updated"""
    _name = "currency.rate.update.service"
    _description = "Currency Rate Update"

    @api.one
    @api.constrains('max_delta_days')
    def _check_max_delta_days(self):
        if self.max_delta_days < 0:
            raise exceptions.Warning(_('Max delta days must be >= 0'))

    @api.one
    @api.constrains('interval_number')
    def _check_interval_number(self):
        if self.interval_number < 0:
            raise exceptions.Warning(_('Interval number must be >= 0'))

    @api.onchange('interval_number')
    def _onchange_interval_number(self):
        if self.interval_number == 0:
            self.note = '%s Service deactivated. Currencies will no longer ' \
                        'be updated. \n%s' % (fields.Datetime.now(),
                                              self.note and self.note or '')

    @api.onchange('service')
    def _onchange_service(self):
        currency_list = ''
        if self.service:
            currencies = []
            getter = CurrencyGetterType.get(self.service)
            currency_list = getter.supported_currency_array
            currencies = self.env['res.currency'].search(
                [('name', 'in', currency_list)])
            self.currency_list = [(6, 0, [curr.id for curr in currencies])]

    def _selection_service(self, *a, **k):
        res = [(x.code, x.name) for x in CurrencyGetterType.getters.values()]
        return res

    # List of webservicies the value sould be a class name
    service = fields.Selection(
        _selection_service,
        string="Webservice to use",
        required=True)
    # List of currencies available on webservice
    currency_list = fields.Many2many('res.currency',
                                     'res_currency_update_avail_rel',
                                     'service_id',
                                     'currency_id',
                                     string='Currencies available')
    # List of currency to update
    currency_to_update = fields.Many2many('res.currency',
                                          'res_currency_auto_update_rel',
                                          'service_id',
                                          'currency_id',
                                          string='Currencies to update with '
                                          'this service')
    # Link with company
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'currency.rate.update.service'))
    # Note fileds that will be used as a logger
    note = fields.Text('Update logs')
    max_delta_days = fields.Integer(
        string='Max delta days', default=4, required=True,
        help="If the time delta between the rate date given by the "
        "webservice and the current date exceeds this value, "
        "then the currency rate is not updated in OpenERP.")
    interval_type = fields.Selection([
        ('days', 'Day(s)'),
        ('weeks', 'Week(s)'),
        ('months', 'Month(s)')],
        string='Currency update frequency',
        default='days')
    interval_number = fields.Integer(string='Frequency', default=1)
    next_run = fields.Date(string='Next run on', default=fields.Date.today())

    _sql_constraints = [('curr_service_unique',
                         'unique (service, company_id)',
                         _('You can use a service only one time per '
                           'company !'))]

    @api.one
    def refresh_currency(self):
        """Refresh the currencies rates !!for all companies now"""
        _logger.info(
            'Starting to refresh currencies with service %s (company: %s)',
            self.service, self.company_id.name)
        rate_obj = self.env['res.currency.rate']
        company = self.company_id
        # The multi company currency can be set or no so we handle
        # The two case
        if company.auto_currency_up:
            main_currency = self.company_id.currency_id
            if not main_currency:
                raise exceptions.Warning(_('There is no main '
                                           'currency defined!'))
            if main_currency.rate != 1:
                raise exceptions.Warning(_('Base currency rate should '
                                           'be 1.00!'))
            note = self.note or ''
            try:
                # We initalize the class that will handle the request
                # and return a dict of rate
                getter = CurrencyGetterType.get(self.service)
                curr_to_fetch = [x.name for x in self.currency_to_update]
                res, log_info = getter.get_updated_currency(
                    curr_to_fetch,
                    main_currency.name,
                    self.max_delta_days
                    )
                rate_name = \
                    fields.Datetime.to_string(datetime.utcnow().replace(
                        hour=0, minute=0, second=0, microsecond=0))
                for curr in self.currency_to_update:
                    if curr.id == main_currency.id:
                        continue
                    do_create = True
                    for rate in curr.rate_ids:
                        if rate.name == rate_name:
                            rate.rate = res[curr.name]
                            do_create = False
                            break
                    if do_create:
                        vals = {
                            'currency_id': curr.id,
                            'rate': res[curr.name],
                            'name': rate_name
                        }
                        rate_obj.create(vals)
                        _logger.info(
                            'Updated currency %s via service %s',
                            curr.name, self.service)

                # Show the most recent note at the top
                msg = '%s \n%s currency updated. %s' % (
                    log_info or '',
                    fields.Datetime.to_string(datetime.today()),
                    note
                )
                self.write({'note': msg})
            except Exception as exc:
                error_msg = '\n%s ERROR : %s %s' % (
                    fields.Datetime.to_string(datetime.today()),
                    repr(exc),
                    note
                )
                _logger.error(repr(exc))
                self.write({'note': error_msg})
            if self._context.get('cron', False):
                midnight = time(0, 0)
                next_run = (datetime.combine(
                            fields.Date.from_string(self.next_run),
                            midnight) +
                            _intervalTypes[str(self.interval_type)]
                            (self.interval_number)).date()
                self.next_run = next_run
        return True

    @api.multi
    def run_currency_update(self):
        # Update currency at the given frequence
        services = self.search([('next_run', '=', fields.Date.today())])
        services.with_context(cron=True).refresh_currency()

    @api.model
    def _run_currency_update(self):
        _logger.info('Starting the currency rate update cron')
        self.run_currency_update()
        _logger.info('End of the currency rate update cron')
