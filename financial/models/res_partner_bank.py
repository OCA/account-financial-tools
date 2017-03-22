# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class ResPartnerBank(models.Model):

    _inherit = 'res.partner.bank'
    # _inherits = ['mail.thread']

    initial_balance = fields.Monetary(
        string=u'Initial Balance',
        track_visibility='onchange',
        default=0.00
    )
    date_balance = fields.Date(
        string=u'Balance date',
        track_visibility='onchange',
        default=fields.Date.context_today,
    )
