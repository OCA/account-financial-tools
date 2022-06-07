# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class AccountPaymentIntransitDeduction(models.Model):
    _name = 'account.payment.intransit.deduction'
    _description = 'Payment Intransit Deduction'

    payment_intransit_id = fields.Many2one(
        comodel_name='account.payment.intransit',
        string='Payment',
        readonly=True,
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='payment_intransit_id.currency_id',
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        domain=[('deprecated', '=', False)],
        required=True,
    )
    amount = fields.Monetary(
        string='Deduction Amount',
        required=True,
    )
    name = fields.Char(
        string='Label',
        required=True,
    )
