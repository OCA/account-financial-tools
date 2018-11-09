# Copyright 2018 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ast import literal_eval
from odoo import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _default_budget_template(self):
        return self.env['crossovered.budget.template'].search([], limit=1)

    budget_templ_id = fields.Many2one(
        comodel_name='crossovered.budget.template',
        string='Default Budget Template',
        default=_default_budget_template)

    @api.model
    def get_values(self):
        res = super(AccountConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        # the value of the parameter is a nonempty string
        budget_templ_id = literal_eval(
            get_param('account_budget_template.budget_template_id',
                      default='False'))
        if (budget_templ_id and
                not self.env['crossovered.budget.template'].sudo().browse(
                    budget_templ_id).exists()):
            budget_templ_id = False
        res.update(
            budget_templ_id=budget_templ_id,
        )
        return res

    @api.multi
    def set_values(self):
        super(AccountConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        # we store the repr of the values, since the value of the parameter is
        # a required string
        set_param('account_budget_template.budget_template_id',
                  repr(self.budget_templ_id.id))
