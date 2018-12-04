# Copyright 2018 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import common
from odoo.exceptions import ValidationError
from odoo import fields

from ..models.crossovered_budget import _periodicityMonths

str2date = fields.Date.from_string


class TestAccountBudgetTemplate(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountBudgetTemplate, cls).setUpClass()
        analytics = cls.env['account.analytic.account'].search([])
        cls.template_obj = cls.env['crossovered.budget.template']
        cls.budget_tmpl = cls.template_obj.create({
            'name': 'Test Budget',
            'budget_post_ids': [
                (0, 0, {'name': 'Test Position',
                        'account_ids': analytics.ids})],
        })
        today = str2date(fields.Date.today())
        start_date = today.replace(day=1, month=1)
        end_date = today.replace(day=29, month=12)
        cls.budget = cls.env['crossovered.budget'].create({
            'name': 'New Budget',
            'budget_tmpl_id': cls.budget_tmpl.id,
            'date_from': start_date,
            'date_to': end_date,
        })
        cls.setting = cls.env['res.config.settings'].create({})

    def test_template_monthly(self):
        self.assertEqual(self.budget_tmpl.periodicity, 'monthly')
        self.assertFalse(self.budget.crossovered_budget_line)
        self.budget.button_compute_lines()
        self.assertEqual(
            len(self.budget.crossovered_budget_line),
            ((12 / _periodicityMonths[self.budget_tmpl.periodicity]) *
             len(self.budget_tmpl.budget_post_ids)))

    def test_template_quaterly(self):
        self.budget_tmpl.periodicity = 'quaterly'
        self.assertFalse(self.budget.crossovered_budget_line)
        self.budget.button_compute_lines()
        self.assertEqual(
            len(self.budget.crossovered_budget_line),
            ((12 / _periodicityMonths[self.budget_tmpl.periodicity]) *
             len(self.budget_tmpl.budget_post_ids)))

    def test_template_sixmonthly(self):
        self.budget_tmpl.periodicity = 'sixmonthly'
        self.assertFalse(self.budget.crossovered_budget_line)
        self.budget.button_compute_lines()
        self.assertEqual(
            len(self.budget.crossovered_budget_line),
            ((12 / _periodicityMonths[self.budget_tmpl.periodicity]) *
             len(self.budget_tmpl.budget_post_ids)))

    def test_template_yearly(self):
        self.budget_tmpl.periodicity = 'yearly'
        self.assertFalse(self.budget.crossovered_budget_line)
        self.budget.button_compute_lines()
        self.assertEqual(
            len(self.budget.crossovered_budget_line),
            ((12 / _periodicityMonths[self.budget_tmpl.periodicity]) *
             len(self.budget_tmpl.budget_post_ids)))

    def test_template_noperiodicity(self):
        self.budget_tmpl.periodicity = False
        self.assertFalse(self.budget.crossovered_budget_line)
        self.budget.button_compute_lines()
        self.assertEqual(
            len(self.budget.crossovered_budget_line),
            len(self.budget_tmpl.budget_post_ids))

    def test_res_config(self):
        self.assertFalse(
            self.setting.budget_templ_id)
        self.setting.budget_templ_id = (
            self.setting._default_budget_template())
        self.setting.set_values()
        self.assertTrue(
            self.setting.budget_templ_id)
        self.setting.budget_templ_id.unlink()
        self.assertFalse(
            self.setting.budget_templ_id)

    def test_budget_template_validation_error(self):
        with self.assertRaises(ValidationError):
            self.template_obj.create({
                'name': 'Test Error',
            })
        with self.assertRaises(ValidationError):
            self.budget_tmpl.write({
                'budget_post_ids': [],
            })
        self.budget_tmpl.write({
            'name': 'Name Change',
        })
