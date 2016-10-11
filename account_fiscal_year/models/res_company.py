# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    def find_daterange_fy(self, date):
        """
        try to find a date range with type 'fiscalyear'
        with @param:date contained in its date_start/date_end interval
        """
        fy_id = self.env.ref('account_fiscal_year.fiscalyear')
        date_str = fields.Datetime.to_string(date)
        s_args = [
            ('type_id', '=', fy_id.id),
            ('date_start', '<=', date_str),
            ('date_end', '>=', date_str),
            ('company_id', '=', self.id),
        ]
        date_range = self.env['date.range'].search(s_args)
        return date_range

    @api.multi
    def compute_fiscalyear_dates(self, date):
        """ Computes the start and end dates of the fiscalyear where the given
            'date' belongs to
            @param date: a datetime object
            @returns: a dictionary with date_from and date_to
        """
        self = self[0]
        date_range = self.find_daterange_fy(date)
        if date_range:
            # do stuff and override 'normal' behaviour
            return {
                'date_from': fields.Date.from_string(date_range[0].date_start),
                'date_to': fields.Date.from_string(date_range[0].date_end),
            }
        else:
            # fall back to standard Odoo computation
            return super(ResCompany, self).compute_fiscalyear_dates(date)
