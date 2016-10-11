# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, exceptions


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    fiscal_year = fields.Boolean(string='Is fiscal year?', default=False)

    @api.multi
    def unlink(self):
        """
        Cannot delete a date_range_type with 'fiscal_year' flag = True
        """
        for rec in self:
            if rec.fiscal_year:
                raise exceptions.ValidationError(
                    _('You cannot delete a date range type with '
                      'flag "fiscal_year"')
                )
            else:
                super(DateRangeType, rec).unlink()
