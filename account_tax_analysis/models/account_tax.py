# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountTax(models.Model):

    _inherit = 'account.tax'

    analysis_name = fields.Char(compute="_compute_analysis_name")

    @api.multi
    @api.depends("name", "description")
    def _compute_analysis_name(self):
        for tax in self:
            if tax.description:
                tax.analysis_name = "%s - %s" % (tax.description, tax.name)
            else:
                tax.analysis_name = tax.name
