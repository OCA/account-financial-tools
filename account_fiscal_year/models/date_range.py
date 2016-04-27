# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models
from openerp.tools import (DEFAULT_SERVER_DATETIME_FORMAT)


class DateRange(models.Model):
    _inherit = 'date.range'

    def find_daterange_fy_start(self, date):
        """
        try to find a date range with type 'fiscalyear'
        with @param:date <= date_start
        """
        fy_id = self.env.ref('account_fiscal_year.fiscalyear')
        date_str = date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        s_args = [
            ('type_id', '=', fy_id.id),
            ('date_start', '<=', date_str),
            ('company_id', '=', self.company_id.id),
        ]
        date_range = self.env['date.range'].search(s_args)
        return date_range.date_start
