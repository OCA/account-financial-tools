# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AccountPaymentMode(models.Model):
    _inherit = 'account.payment.mode'

    interest_percent = fields.Float(
        store=True
    )
    delay_fee_percent = fields.Float(
        store=True
    )
    liquidity = fields.Boolean(
        string=_('Included in credit limit'),
        store=True,
    )
