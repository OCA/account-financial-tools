# -*- coding: utf-8 -*-
# Copyright 2012-2014 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    currency_rate_max_delta = fields.Integer(
        string='Max Time Delta in Days for Currency Rates', default=7,
        help="This is the maximum interval in days between "
        "the date associated with the amount to convert and the date "
        "of the nearest currency rate available in Odoo.")

    _sql_constraints = [
        ('currency_rate_max_delta_positive',
         'CHECK (currency_rate_max_delta >= 0)',
         "The value of the field 'Max Time Delta in Days for Currency Rates' "
         "must be positive or 0."),
    ]
