# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo import exceptions, fields


class TestCurrencyRateUpdate(common.SavepointCase):

    def setUp(self):
        super(TestCurrencyRateUpdate, self).setUp()
        self.env.user.company_id.currency_id = self.env.ref('base.EUR')
        self.currency = self.env.ref('base.USD')
        self.update_service = self.env['currency.rate.update.service'].create({
            'service': 'ECB',
            'currency_to_update':
                [(4, self.currency.id),
                 (4, self.env.user.company_id.currency_id.id)]
        })
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency.id)])
        currency_rates.unlink()

    def test_currency_rate_update_ECB(self):
        self.update_service.refresh_currency()
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency.id)])
        self.assertTrue(currency_rates)

    def test_constrains_max_delta_days(self):
        with self.assertRaises(exceptions.ValidationError):
            self.update_service.write({'max_delta_days': -5})

    def test_constrains_interval_number(self):
        with self.assertRaises(exceptions.ValidationError):
            self.update_service.write({'interval_number': -5})

    def test_onchange_service(self):
        new_service = self.env['currency.rate.update.service'].new(
            {'service': 'ECB'})
        new_service._onchange_service()
        self.assertEqual(len(new_service.currency_list), 2)

    def test_deactivate_update(self):
        before_message_count = len(self.update_service.message_ids)
        self.update_service.write({'interval_number': 0})
        self.assertEqual(before_message_count + 1,
                         len(self.update_service.message_ids))

    def test_currency_rate_update_cron(self):
        self.update_service.next_run = fields.Date.today()
        self.env['currency.rate.update.service']._run_currency_update()
        self.update_service.refresh_currency()
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency.id)])
        self.assertTrue(currency_rates)

    def test_currency_rate_update_USD_EUR(self):
        self.env.user.company_id.currency_id = self.env.ref('base.USD')
        self.euro = self.env.ref('base.EUR')
        self.update_service.write({
            'currency_to_update': [(4, self.euro.id)]
        })
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.euro.id)])
        currency_rates.unlink()
        main_currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.env.user.company_id.currency_id.id)])
        main_currency_rates.unlink()
        self.update_service.refresh_currency()
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.euro.id)])
        self.assertTrue(currency_rates)

    def test_currency_rate_update_USD_CHF(self):
        self.env.user.company_id.currency_id = self.env.ref('base.USD')
        self.chf = self.env.ref('base.CHF')
        self.env.ref('base.CHF').active = True
        self.update_service.write({
            'currency_to_update': [(4, self.chf.id)]
        })
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.chf.id)])
        currency_rates.unlink()
        main_currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.env.user.company_id.currency_id.id)])
        main_currency_rates.unlink()
        self.update_service.refresh_currency()
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.chf.id)])
        self.assertTrue(currency_rates)
