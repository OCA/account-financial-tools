# -*- coding: utf-8 -*-
# Author: Vincent Renaville
# Copyright 2013 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountTaxDeclarationAnalysis(models.TransientModel):
    _name = 'account.vat.declaration.analysis'
    _description = 'Account Vat Declaration'

    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    date_range_id = fields.Many2one(
        comodel_name='date.range', string='Date Range', ondelete="cascade")
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries'),
    ], 'Target Moves', required=True, default='posted')
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company", ondelete="cascade",
        default=lambda s: s._default_company_id())

    @api.model
    def _default_company_id(self):
        return self.env["res.company"]._company_default_get()

    @api.multi
    def show_vat(self):
        self.ensure_one()

        action = self.env.ref('account_tax_analysis.action_view_tax_analysis')
        action_fields = action.read()[0]

        domain = [('date', '>=', self.start_date),
                  ('date', '<=', self.end_date)]
        if self.company_id:
            domain.append(("company_id", "=", self.company_id.id))
        action_fields['domain'] = domain

        context = {'search_default_group_by_tax_type': 1}
        if self.target_move == 'posted':
            context['search_default_posted'] = 1
        action_fields['context'] = context

        return action_fields

    @api.onchange('date_range_id')
    def _onchange_date_range(self):
        if self.date_range_id:
            self.start_date = self.date_range_id.date_start
            self.end_date = self.date_range_id.date_end

    @api.onchange('start_date', 'end_date')
    def _onchange_dates(self):
        if self.date_range_id:
            if self.start_date != self.date_range_id.date_start or \
                    self.end_date != self.date_range_id.date_end:
                self.date_range_id = False
