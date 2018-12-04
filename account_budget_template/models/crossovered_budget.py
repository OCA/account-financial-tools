# Copyright 2018 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ast import literal_eval
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

from_string = fields.Date.from_string
to_string = fields.Date.to_string

_periodicityMonths = {
    'monthly': 1,
    'quaterly': 3,
    'sixmonthly': 6,
    'yearly': 12,
}


class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'

    def _default_budget_tmpl_id(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        default_tmpl_id = literal_eval(
            get_param('account_budget_template.budget_template_id', 'False'))
        return self.env['crossovered.budget.template'].browse(default_tmpl_id)

    budget_tmpl_id = fields.Many2one(
        comodel_name='crossovered.budget.template', string='Template',
        default=_default_budget_tmpl_id)

    @api.multi
    def button_compute_lines(self):
        for budget in self.filtered('budget_tmpl_id'):
            budget.action_create_period()

    def action_create_period(self):
        budget_line_obj = self.env['crossovered.budget.lines']
        for budget in self.filtered(lambda b: not b.crossovered_budget_line and
                                    b.state == 'draft'):
            budget_posts = budget.budget_tmpl_id.budget_post_ids
            periodicity_months = False
            if budget.budget_tmpl_id.periodicity:
                periodicity_months = (
                    _periodicityMonths[budget.budget_tmpl_id.periodicity])
            vals = {
                'crossovered_budget_id': budget.id,
                'planned_amount': 0.0,
            }
            if not periodicity_months:
                for budget_post in budget_posts:
                    vals.update({
                        'date_from': budget.date_from,
                        'date_to': budget.date_to,
                        'general_budget_id': budget_post.id,
                    })
                    budget_line_obj.create(vals)
            else:
                ds = from_string(budget.date_from)
                while to_string(ds) < budget.date_to:
                    de = ds + relativedelta(months=periodicity_months, days=-1)
                    if to_string(de) > budget.date_to:
                        de = from_string(budget.date_to)
                    for budget_post in budget_posts:
                        vals.update({
                            'date_from': to_string(ds),
                            'date_to': to_string(de),
                            'general_budget_id': budget_post.id,
                        })
                        budget_line_obj.create(vals)
                    ds = ds + relativedelta(months=periodicity_months)
        return True
