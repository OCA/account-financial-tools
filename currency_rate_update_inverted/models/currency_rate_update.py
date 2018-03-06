# © 2017 Komit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


from odoo.addons.currency_rate_update.services.currency_getter_interface \
    import CurrencyGetterType


_logger = logging.getLogger(__name__)

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
}


class CurrencyRateUpdateService(models.Model):

    _inherit = "currency.rate.update.service"

    @api.multi
    def refresh_currency(self):
        """Refresh the currencies rates !!for all companies now"""
        rate_obj = self.env['res.currency.rate']
        for srv in self:
            _logger.info(
                'Starting to refresh currencies with service %s (company: %s)',
                srv.service, srv.company_id.name)
            company = srv.company_id
            # The multi company currency can be set or no so we handle
            # The two case
            if company.auto_currency_up:
                main_currency = company.currency_id
                # No need to test if main_currency exists, because it is a
                # required field
                if float_compare(
                        main_currency.rate, 1,
                        precision_rounding=main_currency.rounding):
                    raise UserError(_(
                        "In company '%s', the rate of the main currency (%s) "
                        "must be 1.00 (current rate: %s).") % (
                                        company.name,
                                        main_currency.name,
                                        main_currency.rate))
                try:
                    # We initalize the class that will handle the request
                    # and return a dict of rate
                    getter = CurrencyGetterType.get(srv.service)
                    curr_to_fetch = [x.name for x in srv.currency_to_update]
                    res, log_info = getter.get_updated_currency(
                        curr_to_fetch,
                        main_currency.name,
                        srv.max_delta_days
                    )
                    rate_name = \
                        fields.Datetime.to_string(datetime.utcnow().replace(
                            hour=0, minute=0, second=0, microsecond=0))
                    for curr in srv.currency_to_update:
                        if curr == main_currency:
                            continue
                        rates = rate_obj.search([
                            ('currency_id', '=', curr.id),
                            ('company_id', '=', company.id),
                            ('name', '=', rate_name)])
                        if not rates:
                            rate = (curr.rate_inverted
                                    and 1 / res[curr.name]
                                    or res[curr.name])
                            vals = {
                                'currency_id': curr.id,
                                'rate': rate,
                                'name': rate_name,
                                'company_id': company.id,
                            }
                            rate_obj.create(vals)
                            _logger.info(
                                'Updated currency %s via service %s '
                                'in company %s',
                                curr.name, srv.service, company.name)

                    # Show the most recent note at the top
                    msg = '%s <br/>%s currency updated.' % (
                        log_info or '',
                        fields.Datetime.to_string(datetime.today())
                    )
                    srv.message_post(body=msg)
                except Exception as exc:
                    error_msg = '%s ERROR: %s' % (
                        fields.Datetime.to_string(datetime.today()),
                        repr(exc)
                    )
                    _logger.error(repr(exc))
                    srv.message_post(body=error_msg,
                                     message_type='comment',
                                     subtype='mt_comment')
                if self._context.get('cron'):
                    midnight = time(0, 0)
                    next_run = (datetime.combine(
                        fields.Date.from_string(srv.next_run),
                        midnight) +
                                _intervalTypes[str(srv.interval_type)]
                                (srv.interval_number)).date()
                    srv.next_run = next_run
        return True
