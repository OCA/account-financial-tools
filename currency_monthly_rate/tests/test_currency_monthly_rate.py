# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
from odoo.tests.common import SavepointCase


class TestCurrencyMonthlyRate(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.usd = cls.env.ref('base.USD')
        cls.eur = cls.env.ref('base.EUR')

        # as fields.Date.today() only calls date.today() and then converts it
        # to ORM format string, we don't need it here
        cls.year = str(date.today().year)

        monthly_rate = cls.env['res.currency.rate.monthly']
        rate = cls.env['res.currency.rate']

        monthly_rates_to_create = [
            {'month': '01', 'rate': 1.20},
            {'month': '02', 'rate': 1.40},
        ]
        for r in monthly_rates_to_create:
            r.update({
                'year': cls.year,
                'currency_id': cls.usd.id
            })
            monthly_rate.create(r)

        rates_to_create = [
            {'name': '%s-01-01' % cls.year, 'rate': 1.15},
            {'name': '%s-01-11' % cls.year, 'rate': 1.10},
            {'name': '%s-01-31' % cls.year, 'rate': 1.35},
            {'name': '%s-02-01' % cls.year, 'rate': 1.50},
            {'name': '%s-02-11' % cls.year, 'rate': 1.30},
        ]
        for r in rates_to_create:
            r.update({
                'currency_id': cls.usd.id
            })
            rate.create(r)

        cls.jan_2 = '%s-01-02' % cls.year
        cls.jan_12 = '%s-01-12' % cls.year
        cls.jan_31 = '%s-01-31' % cls.year
        cls.feb_2 = '%s-02-02' % cls.year
        cls.feb_12 = '%s-02-12' % cls.year

    def compute_eur_usd(self, amount, date_, monthly):
        self.usd.invalidate_cache()
        self.eur.invalidate_cache()
        if monthly:
            return self.eur.with_context(
                date=date_, monthly_rate=True
            ).compute(amount, self.usd)
        else:
            return self.eur.with_context(
                date=date_
            ).compute(amount, self.usd)

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

    def test_monthly_rate(self):
        self.assertEqual(self.usd.with_context(date=self.jan_2).monthly_rate,
                         1.2)
        self.assertEqual(self.usd.with_context(date=self.feb_2).monthly_rate,
                         1.4)
