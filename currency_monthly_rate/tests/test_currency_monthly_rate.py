# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo import fields


class TestCurrencyMonthlyRate(TransactionCase):

    def setUp(self):
        super(TestCurrencyMonthlyRate, self).setUp()

        self.usd = self.env.ref('base.USD')
        self.eur = self.env.ref('base.EUR')

        self.year = str(fields.Date.from_string(fields.Date.today()).year)

        monthly_rate = self.env['res.currency.rate.monthly']
        rate = self.env['res.currency.rate']

        monthly_rates_to_create = [
            {'month': '01', 'rate': 1.20},
            {'month': '02', 'rate': 1.40},
        ]
        for r in monthly_rates_to_create:
            r.update({
                'year': self.year,
                'currency_id': self.usd.id
            })
            monthly_rate.create(r)

        rates_to_create = [
            {'name': '%s-01-01' % self.year, 'rate': 1.15},
            {'name': '%s-01-11' % self.year, 'rate': 1.10},
            {'name': '%s-01-31' % self.year, 'rate': 1.35},
            {'name': '%s-02-01' % self.year, 'rate': 1.50},
            {'name': '%s-02-11' % self.year, 'rate': 1.30},
        ]
        for r in rates_to_create:
            r.update({
                'currency_id': self.usd.id
            })
            rate.create(r)

        self.jan_2 = '%s-01-02' % self.year
        self.jan_12 = '%s-01-12' % self.year
        self.jan_31 = '%s-01-31' % self.year
        self.feb_2 = '%s-02-02' % self.year
        self.feb_12 = '%s-02-12' % self.year

    def compute_eur_usd(self, amount, date, monthly):
        self.usd.invalidate_cache()
        self.eur.invalidate_cache()
        if monthly:
            return self.eur.with_context(date=date, monthly_rate=True).compute(
                amount, self.usd)
        else:
            return self.eur.with_context(date=date).compute(amount, self.usd)

    def test_monthly_compute(self):
        self.assertEqual(self.compute_eur_usd(10, self.jan_2, True), 12)
        self.assertEqual(self.compute_eur_usd(10, self.jan_12, True), 12)
        self.assertEqual(self.compute_eur_usd(10, self.jan_31, True), 12)
        self.assertEqual(self.compute_eur_usd(10, self.feb_2, True), 14)
        self.assertEqual(self.compute_eur_usd(10, self.feb_12, True), 14)

    def test_standard_compute(self):
        self.assertEqual(self.compute_eur_usd(10, self.jan_2, False), 11.5)
        self.assertEqual(self.compute_eur_usd(10, self.jan_12, False), 11)
        self.assertEqual(self.compute_eur_usd(10, self.jan_31, False), 13.5)
        self.assertEqual(self.compute_eur_usd(10, self.feb_2, False), 15)
        self.assertEqual(self.compute_eur_usd(10, self.feb_12, False), 13)
