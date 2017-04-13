# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    interest_percent = fields.Float(
        string=u'Interest (%)',
    )
    delay_fee_percent = fields.Float(
        string=u'Delay fee (%)',
    )
    liquidity = fields.Boolean(
        string=u'Included in credit limit',
    )
    compensation_days = fields.Integer(
        string=u'Days elapsed to compensate the payment',
    )
