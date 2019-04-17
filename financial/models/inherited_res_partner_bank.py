# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    initial_balance = fields.Monetary(
        track_visibility='onchange',
        digits=(18, 2),
    )
    date_balance = fields.Date(
        track_visibility='onchange',
        default=fields.Date.context_today,
    )
