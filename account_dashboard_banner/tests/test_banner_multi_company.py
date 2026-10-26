# Copyright 2026 Altixia (https://altixia.com/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged
from odoo.tools.misc import format_amount, format_date
from odoo.tools.safe_eval import safe_eval

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountDashboardBannerMultiCompany(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.company_data["company"]
        cls.company_b = cls.setup_other_company(name="Banner Company B")["company"]
        eur = cls.env.ref("base.EUR")
        eur.active = True
        cls.company_eur = cls.setup_other_company(
            name="Banner Company EUR", currency_id=eur.id
        )["company"]
        cell_obj = cls.env["account.dashboard.banner.cell"]
        cell_obj.search([]).unlink()
        cls.cell_debt = cell_obj.create(
            {
                "cell_type": "customer_debt",
                "sequence": 10,
                "warn": True,
                "warn_type": "under",
                "warn_min": 50,
            }
        )
        cls.cell_lock = cell_obj.create(
            {"cell_type": "fiscalyear_lock_date", "sequence": 20, "warn": True}
        )
        cls.cell_overdue = cell_obj.create(
            {
                "cell_type": "customer_overdue",
                "sequence": 30,
                "custom_tooltip": "TEST custom tooltip",
            }
        )
        cls.invoice_a = cls.init_invoice(
            "out_invoice", amounts=[100.0], taxes=[], post=True, company=cls.company_a
        )
        cls.invoice_b = cls.init_invoice(
            "out_invoice", amounts=[20.0], taxes=[], post=True, company=cls.company_b
        )
        cls.invoice_eur = cls.init_invoice(
            "out_invoice", amounts=[300.0], taxes=[], post=True, company=cls.company_eur
        )

    def _banner(self, companies, currency=None):
        cell_obj = self.env["account.dashboard.banner.cell"].with_context(
            allowed_company_ids=companies.ids
        )
        return {
            cell_data["cell_type"]: cell_data
            for cell_data in cell_obj.get_banner_data(
                currency_id=currency and currency.id
            ).values()
        }

    def test_single_company_unchanged(self):
        cell_obj = self.env["account.dashboard.banner.cell"].with_company(
            self.company_b
        )
        expected = cell_obj.with_context(
            allowed_company_ids=self.company_b.ids
        )._prepare_banner_data(self.company_b)
        res = cell_obj.with_context(
            allowed_company_ids=self.company_b.ids
        ).get_banner_data()
        self.assertEqual(res, expected)

    def test_same_currency_total(self):
        banner = self._banner(self.company_a | self.company_b)
        debt = banner["customer_debt"]
        self.assertAlmostEqual(debt["raw_value"], 120.0)
        self.assertEqual(
            debt["value"], format_amount(self.env, 120.0, self.company_a.currency_id)
        )
        # one total, no line per company
        self.assertNotIn("details", debt)
        # each company computed as if it were alone, its own receivable account
        self.assertEqual(
            self._banner(self.company_b)["customer_debt"]["raw_value"], 20.0
        )

    def test_different_currencies_converted_at_today_rate(self):
        eur = self.company_eur.currency_id
        rate_obj = self.env["res.currency.rate"]
        # an old rate and today's rate: today's rate is the one used
        rate_obj.create(
            {
                "name": "2019-01-01",
                "rate": 0.25,
                "currency_id": eur.id,
                "company_id": self.company_a.id,
            }
        )
        rate_obj.create(
            {
                "name": fields.Date.context_today(self.env.user),
                "rate": 0.5,
                "currency_id": eur.id,
                "company_id": self.company_a.id,
            }
        )
        companies = self.company_a | self.company_b | self.company_eur
        debt = self._banner(companies)["customer_debt"]
        # 100 + 20 USD + 300 EUR at 0.5 EUR per USD = 720 USD, one total in the
        # currency of the current company (company A)
        self.assertAlmostEqual(debt["raw_value"], 720.0)
        self.assertEqual(
            debt["value"], format_amount(self.env, 720.0, self.company_a.currency_id)
        )
        self.assertIn("latest known rate", debt["tooltip"])

    def test_total_in_the_currency_of_the_current_company(self):
        usd = self.company_a.currency_id
        eur = self.company_eur.currency_id
        self.env["res.currency.rate"].create(
            {
                "name": fields.Date.context_today(self.env.user),
                "rate": 2.0,
                "currency_id": usd.id,
                "company_id": self.company_eur.id,
            }
        )
        # the EUR company is the current one: 300 EUR + 100 USD at 2 USD per EUR
        cell_obj = self.env["account.dashboard.banner.cell"].with_context(
            allowed_company_ids=[self.company_eur.id, self.company_a.id]
        )
        banner = {
            cell_data["cell_type"]: cell_data
            for cell_data in cell_obj.get_banner_data().values()
        }
        debt = banner["customer_debt"]
        self.assertAlmostEqual(debt["raw_value"], 350.0)
        self.assertEqual(debt["value"], format_amount(self.env, 350.0, eur))

    def test_lock_dates_per_company(self):
        recent = fields.Date.context_today(self.env.user) - relativedelta(days=10)
        old = fields.Date.from_string("2019-06-30")
        self.company_a.fiscalyear_lock_date = recent
        self.company_b.fiscalyear_lock_date = old
        lock = self._banner(self.company_a | self.company_b)["fiscalyear_lock_date"]
        self.assertEqual(lock["raw_value"], old)
        self.assertEqual(lock["value"], format_date(self.env, old))
        self.assertIn("per company", lock["tooltip"])
        # only company B is late: the cell warns
        self.assertTrue(lock["warn"])
        self.assertFalse(self._banner(self.company_a)["fiscalyear_lock_date"]["warn"])
        self.company_b.fiscalyear_lock_date = recent
        lock = self._banner(self.company_a | self.company_b)["fiscalyear_lock_date"]
        self.assertEqual(lock["raw_value"], recent)
        self.assertFalse(lock["warn"])
        # a company without lock date: nothing is locked in all companies
        lock = self._banner(self.company_a | self.company_b | self.company_eur)[
            "fiscalyear_lock_date"
        ]
        self.assertIs(lock["raw_value"], False)
        self.assertTrue(lock["warn"])

    def test_amount_warning_per_company(self):
        # the total (120) is above the minimum (50) but company B (20) is not
        debt = self._banner(self.company_a | self.company_b)["customer_debt"]
        self.assertTrue(debt["warn"])
        self.assertFalse(self._banner(self.company_a)["customer_debt"]["warn"])

    def test_custom_tooltip_kept(self):
        overdue = self._banner(self.company_a | self.company_b)["customer_overdue"]
        self.assertEqual(overdue["tooltip"], "TEST custom tooltip")
        debt = self._banner(self.company_a | self.company_b)["customer_debt"]
        self.assertIn("converted", debt["tooltip"])

    def test_other_cell_types_keep_the_current_company_value(self):
        # a cell type added by another module (e.g. a MIS Builder KPI) is not an
        # amount of the module: never converted nor summed
        cell_class = type(self.env["account.dashboard.banner.cell"])
        with patch.object(cell_class, "_get_amount_cell_types", return_value=[]):
            debt = self._banner(self.company_eur | self.company_a)["customer_debt"]
        alone = self._banner(self.company_eur)["customer_debt"]
        self.assertEqual(debt["value"], alone["value"])
        self.assertEqual(debt["raw_value"], alone["raw_value"])
        self.assertEqual(debt["tooltip"], alone["tooltip"])

    def test_banner_currencies(self):
        cell_obj = self.env["account.dashboard.banner.cell"]
        usd = self.company_a.currency_id
        eur = self.company_eur.currency_id
        # one currency: nothing to choose
        res = cell_obj.with_context(
            allowed_company_ids=[self.company_a.id, self.company_b.id]
        ).get_banner_currencies()
        self.assertEqual(res, [{"id": usd.id, "name": usd.name}])
        # several currencies: the one of the current company first
        res = cell_obj.with_context(
            allowed_company_ids=[self.company_eur.id, self.company_a.id]
        ).get_banner_currencies()
        self.assertEqual([cur["id"] for cur in res], [eur.id, usd.id])
        res = cell_obj.with_context(
            allowed_company_ids=[self.company_a.id, self.company_eur.id]
        ).get_banner_currencies()
        self.assertEqual([cur["id"] for cur in res], [usd.id, eur.id])

    def test_total_in_the_chosen_currency(self):
        eur = self.company_eur.currency_id
        self.env["res.currency.rate"].create(
            {
                "name": fields.Date.context_today(self.env.user),
                "rate": 0.5,
                "currency_id": eur.id,
                "company_id": self.company_a.id,
            }
        )
        companies = self.company_a | self.company_b | self.company_eur
        debt = self._banner(companies, currency=eur)["customer_debt"]
        # 300 EUR taken as is + 120 USD at 0.5 EUR per USD = 360 EUR
        self.assertAlmostEqual(debt["raw_value"], 360.0)
        self.assertEqual(debt["value"], format_amount(self.env, 360.0, eur))
        self.assertIn("EUR", debt["tooltip"])

    def test_currency_outside_the_companies_refused(self):
        gbp = self.env.ref("base.GBP")
        gbp.active = True
        self.env["res.currency.rate"].create(
            {
                "name": fields.Date.context_today(self.env.user),
                "rate": 0.5,
                "currency_id": gbp.id,
                "company_id": self.company_a.id,
            }
        )
        debt = self._banner(self.company_a | self.company_b, currency=gbp)[
            "customer_debt"
        ]
        # GBP is the currency of none of the selected companies: USD, the
        # currency of the current company, is used instead
        self.assertAlmostEqual(debt["raw_value"], 120.0)
        self.assertEqual(
            debt["value"], format_amount(self.env, 120.0, self.company_a.currency_id)
        )

    def test_hidden_cell_not_in_banner(self):
        self.cell_lock.active = False
        for companies in (self.company_a, self.company_a | self.company_b):
            banner = self._banner(companies)
            self.assertNotIn("fiscalyear_lock_date", banner)
            self.assertIn("customer_debt", banner)
        # still listed in the configuration, to be displayed again
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account_dashboard_banner.account_dashboard_banner_cell_action"
        )
        cells = self.env["account.dashboard.banner.cell"].with_context(
            **safe_eval(action["context"])
        )
        self.assertIn(self.cell_lock, cells.search([]))
        self.cell_lock.active = True
        self.assertIn("fiscalyear_lock_date", self._banner(self.company_a))
