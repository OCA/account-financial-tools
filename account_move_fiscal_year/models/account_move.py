# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class AccountMove(models.Model):

    _inherit = 'account.move'

    date_range_fy_id = fields.Many2one(
        comodel_name='date.range', string="Fiscal year",
        domain=lambda self: self._get_date_range_fy_domain(),
        compute='_compute_date_range_fy', search='_search_date_range_fy')

    @api.model
    def _get_date_range_fy_domain(self):
        fiscal_year_type = self.env.ref('account_fiscal_year.fiscalyear')
        return "[('type_id', '=', %d)]" % fiscal_year_type.id

    @api.multi
    @api.depends('date', 'company_id')
    def _compute_date_range_fy(self):
        for rec in self:
            date = fields.Date.from_string(rec.date)
            company = rec.company_id
            rec.date_range_fy_id =\
                company and company.find_daterange_fy(date) or False

    @api.model
    def _search_date_range_fy(self, operator, value):
        if operator in ('=', '!=', 'in', 'not in'):
            date_range_domain = [('id', operator, value)]
        else:
            date_range_domain = [('name', operator, value)]

        fiscal_year_type = self.env.ref('account_fiscal_year.fiscalyear')
        date_range_domain.append(('type_id', '=', fiscal_year_type.id))
        date_ranges = self.env['date.range'].search(date_range_domain)

        domain = []
        for date_range in date_ranges:
            domain = expression.OR([domain, [
                '&',
                '&',
                ('date', '>=', date_range.date_start),
                ('date', '<=', date_range.date_end),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', date_range.company_id.id),
            ]])
        return domain
