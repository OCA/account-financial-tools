# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, api, _, exceptions


class DateRange(models.Model):
    _inherit = 'date.range'

    @api.multi
    def unlink(self):
        """
        Cannot delete a date_range of type 'fiscal_year'
        """
        for rec in self:
            if rec.type_id.fiscal_year:
                raise exceptions.ValidationError(
                    _('You cannot delete a date range of type "fiscal_year"')
                )
            else:
                super(DateRange, rec).unlink()
