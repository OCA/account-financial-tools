# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    bank_receipt_offsetting_account = fields.Selection([
        ('bank_account', 'Bank Account'),
        ('transfer_account', 'Transfer Account')],
        string='Bank Receipt Offsetting Account',
        default='bank_account'
    )
    bank_receipt_transfer_account_id = fields.Many2one(
        'account.account',
        string='Transfer Account for Bank Receipt',
        ondelete='restrict',
        copy=False,
        domain=[('reconcile', '=', True), ('deprecated', '=', False)]
    )
    bank_receipt_post_move = fields.Boolean(
        string='Post Move for Bank Receipt'
    )
