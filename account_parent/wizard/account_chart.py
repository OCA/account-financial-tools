# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 Steigend IT Solutions
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################

from odoo import models, fields, api, _


class OpenAccountChart(models.TransientModel):
    """
    For Chart of Accounts
    """
    _name = "account.open.chart"
    _description = "Account Open chart"

    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True, default=lambda self: self.env.user.company_id)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    parent_needed = fields.Boolean('Parent Grouping Needed')

    def _build_contexts(self, data):
        result = {}
        result['state'] = data['target_move'] or ''
        result['date_from'] = data['date_from'] or False
        result['date_to'] = data['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        result['show_parent_account'] = True
        return result

    @api.multi
    def account_chart_open_window(self):
        """
        Opens chart of Accounts
        @return: dictionary of Open account chart window on given date(s) and all Entries or posted entries
        """
        self.ensure_one()
        data = self.read([])[0]
        used_context = self._build_contexts(data)
        self = self.with_context(used_context)
        if self.env['account.account'].search([('parent_id', '!=', False)], limit=1):
            result = self.env.ref(
                'account_parent.open_view_account_tree').read([])[0]
        else:
            result = self.env.ref(
                'account_parent.open_view_account_noparent_tree').read([])[0]
        result_context = eval(result.get('context', '{}')) or {}
        used_context.update(result_context)
        result['context'] = str(used_context)
        return result


class WizardMultiChartsAccounts(models.TransientModel):
    _inherit = 'wizard.multi.charts.accounts'

    @api.multi
    def execute(self):
        res = super(WizardMultiChartsAccounts, self).execute()
        self.chart_template_id.update_generated_account(
            {}, self.code_digits, self.company_id)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
