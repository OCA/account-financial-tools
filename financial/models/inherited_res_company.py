# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    today_date = fields.Date(
        string='Today Date',
    )

    def cron_update_reference_date_today(self):
        for company in self.env['res.company'].search([]):
            company.today_date = fields.Date.today()
