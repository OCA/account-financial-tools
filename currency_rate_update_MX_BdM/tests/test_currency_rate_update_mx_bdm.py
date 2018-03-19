# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestCurrencyRateUpdateMxBdm(common.SavepointCase):

    def setUp(self):
        super(TestCurrencyRateUpdateMxBdm, self).setUp()
        self.env.ref('base.MXN').active = True
        self.env.user.company_id.currency_id = self.env.ref('base.MXN')
        self.currency = self.env.ref('base.USD')
        main_currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.env.user.company_id.currency_id.id)])
        main_currency_rates.unlink()
        self.update_service = self.env['currency.rate.update.service'].create({
            'service': 'MX_BdM',
            'currency_to_update': [(4, self.currency.id)]
        })
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency.id)])
        currency_rates.unlink()

    def test_currency_rate_update_MXN_USD(self):
        self.update_service.refresh_currency()
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency.id)])
        self.assertTrue(currency_rates)

    def test_currency_rate_update_USD_MXN(self):
        self.env.user.company_id.currency_id = self.env.ref('base.USD')
        self.mxn = self.env.ref('base.MXN')
        self.update_service.write({
            'currency_to_update': [(4, self.mxn.id)]
        })
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.mxn.id)])
        currency_rates.unlink()
        main_currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.env.user.company_id.currency_id.id)])
        main_currency_rates.unlink()
        self.update_service.refresh_currency()
        currency_rates = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.mxn.id)])
        self.assertTrue(currency_rates)
