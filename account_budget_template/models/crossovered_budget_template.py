# Copyright 2018 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrossoveredBudgetTemplate(models.Model):
    _name = 'crossovered.budget.template'
    _description = 'Budget Template'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    budget_post_ids = fields.Many2many(
        comodel_name='account.budget.post',
        relation='rel_template_budget_post', column1='post_id',
        column2='tmpl_id', string='Budgetary Positions')
    periodicity = fields.Selection(
        selection=[('monthly', 'Monthly'),
                   ('quaterly', 'Quaterly'),
                   ('sixmonthly', 'Six-monthly'),
                   ('yearly', 'Yearly')],
        default='monthly', string='Periodicity')

    def _check_budget_post_ids(self, vals):
        # Raise an error to prevent the account.budget.template to have not
        # specified budget_post_ids. This check is done on create because
        # require=True doesn't work on Many2many fields.
        if 'budget_post_ids' in vals:
            budget_post_ids = self.resolve_2many_commands(
                'budget_post_ids', vals['budget_post_ids'])
        else:
            budget_post_ids = self.budget_post_ids
        if not budget_post_ids:
            raise ValidationError(
                _('The budget template must have at least one budgetary'
                  ' position.'))

    @api.model
    def create(self, vals):
        self._check_budget_post_ids(vals)
        return super(CrossoveredBudgetTemplate, self).create(vals)

    @api.multi
    def write(self, vals):
        self._check_budget_post_ids(vals)
        return super(CrossoveredBudgetTemplate, self).write(vals)
