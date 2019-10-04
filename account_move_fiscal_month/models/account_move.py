# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class AccountMove(models.Model):

    _inherit = 'account.move'

    date_range_fm_id = fields.Many2one(
        comodel_name='date.range', string="Fiscal month",
        domain=lambda self: self._get_date_range_fm_domain(),
        compute='_compute_date_range_fm', search='_search_date_range_fm')

    @api.model
    def _get_date_range_fm_domain(self):
        fiscal_month_type = self.env.ref(
            'account_fiscal_month.date_range_fiscal_month')
        return "[('type_id', '=', %d)]" % fiscal_month_type.id

    @api.multi
    @api.depends('date', 'company_id')
    def _compute_date_range_fm(self):
        for rec in self:
            date = rec.date
            company = rec.company_id
            rec.date_range_fm_id =\
                company and company.find_daterange_fm(date) or False

    @api.model
    def _search_date_range_fm(self, operator, value):
        if operator in ('=', '!=', 'in', 'not in'):
            date_range_domain = [('id', operator, value)]
        else:
            date_range_domain = [('name', operator, value)]

        fiscal_month_type = self.env.ref(
            'account_fiscal_month.date_range_fiscal_month')
        date_range_domain.append(('type_id', '=', fiscal_month_type.id))
        date_ranges = self.env['date.range'].search(date_range_domain)

        if not date_ranges:
            return [('id', '=', False)]

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
