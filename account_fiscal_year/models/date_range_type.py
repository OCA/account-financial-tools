# -*- coding: utf-8 -*-
# Author: Damien Crier
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class DateRangeType(models.Model):
    _inherit = "date.range.type"

    fiscal_year = fields.Boolean(string='Is fiscal year ?', default=False)
