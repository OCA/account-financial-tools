# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestCurrencyRateUpdateRoBnr(common.SavepointCase):

    def setUp(self):
        super(TestCurrencyRateUpdateRoBnr, self).setUp()
        self.env.ref('base.RON').active = True
        self.env.user.company_id.currency_id = self.env.ref('base.RON')
        main_currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.env.user.company_id.currency_id.id)])
        main_currency_rates.unlink()
        self.euro = self.env.ref('base.EUR')
        self.update_service = self.env['currency.rate.update.service'].create({
            'service': 'RO_BNR',
            'currency_to_update': [(4, self.euro.id)]
        })
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.euro.id)])
        currency_rates.unlink()

    def test_currency_rate_update_RON_EUR(self):
        self.update_service.refresh_currency()
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.euro.id)])
        self.assertTrue(currency_rates)

    def test_currency_rate_update_EUR_USD(self):
        self.env.user.company_id.currency_id = self.euro
        self.usd = self.env.ref('base.USD')
        self.update_service.write({
            'currency_to_update': [(4, self.usd.id)]
        })
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.usd.id)])
        currency_rates.unlink()
        main_currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.env.user.company_id.currency_id.id)])
        main_currency_rates.unlink()
        self.update_service.refresh_currency()
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.usd.id)])
        self.assertTrue(currency_rates)

    def test_currency_rate_update_EUR_RON(self):
        self.env.user.company_id.currency_id = self.euro
        self.ron = self.env.ref('base.RON')
        self.update_service.write({
            'currency_to_update': [(4, self.ron.id)]
        })
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.ron.id)])
        currency_rates.unlink()
        main_currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.env.user.company_id.currency_id.id)])
        main_currency_rates.unlink()
        self.update_service.refresh_currency()
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.ron.id)])
        self.assertTrue(currency_rates)
