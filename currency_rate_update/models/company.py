# -*- coding: utf-8 -*-
# © 2009-2016 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    # Activate the currency update
    auto_currency_up = fields.Boolean(
        string='Automatic Currency Rates Download', default=True,
        help="Automatic download of currency rates for this company")
