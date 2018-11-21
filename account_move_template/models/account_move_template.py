# Copyright 2015-2018 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class AccountMoveTemplate(models.Model):
    _name = 'account.move.template'
    _inherit = ['account.document.template',
                # 'mail.activity.mixin',  TODO:  uncomment for saas-15
                'mail.thread']

    @api.model
    def _company_get(self):
        return self.env['res.company']._company_default_get(
            object='account.move.template'
        )

    company_id = fields.Many2one(
        'res.company',
        required=True,
        change_default=True,
        default=_company_get,
    )
    journal_id = fields.Many2one('account.journal', required=True)
    template_line_ids = fields.One2many(
        'account.move.template.line',
        inverse_name='template_id',
    )

    @api.multi
    def action_run_template(self):
        self.ensure_one()
        action = self.env.ref(
            'account_move_template.action_wizard_select_template').read()[0]
        action.update({'context': {'default_template_id': self.id}})
        return action

    _sql_constraints = [
        ('sequence_move_template_uniq', 'unique (name,company_id)',
         'The name of the template must be unique per company !')
    ]


class AccountMoveTemplateLine(models.Model):
    _name = 'account.move.template.line'
    _inherit = 'account.document.template.line'

    company_id = fields.Many2one('res.company',
                                 related='template_id.company_id',
                                 readonly=True)
    journal_id = fields.Many2one('account.journal',
                                 related='template_id.journal_id',
                                 store=True, readonly=True)
    account_id = fields.Many2one(
        'account.account',
        required=True,
        ondelete="cascade"
    )
    partner_id = fields.Many2one('res.partner', string='Partner')
    move_line_type = fields.Selection(
        [('cr', 'Credit'), ('dr', 'Debit')],
        required=True
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        ondelete="cascade"
    )
    analytic_tag_ids = fields.Many2many('account.analytic.tag',
                                        string='Analytic tags')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    tax_line_id = fields.Many2one('account.tax', string='Originator tax',
                                  ondelete='restrict')
    template_id = fields.Many2one('account.move.template')

    _sql_constraints = [
        ('sequence_template_uniq', 'unique (template_id,sequence)',
         'The sequence of the line must be unique per template !')
    ]
