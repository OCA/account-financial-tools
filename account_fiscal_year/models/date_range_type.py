# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _, exceptions


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    fiscal_year = fields.Boolean(string='Is fiscal year ?', default=False)
    accounting = fields.Boolean(string='Is accounting ?', default=False)

    @api.multi
    def unlink(self):
        """
        Cannot delete a date_range_type with 'accounting' flag = True
        """
        for rec in self:
            if rec.accounting:
                raise exceptions.ValidationError(
                    _('You cannot delete a date range type with '
                      'flag "accounting"')
                )
            else:
                super(DateRangeType, rec).unlink()
