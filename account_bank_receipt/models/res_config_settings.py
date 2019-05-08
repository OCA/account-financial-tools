# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bank_receipt_offsetting_account = fields.Selection(
        related='company_id.bank_receipt_offsetting_account',
        readonly=False,
    )
    bank_receipt_transfer_account_id = fields.Many2one(
        related='company_id.bank_receipt_transfer_account_id',
        readonly=False,
    )
    bank_receipt_post_move = fields.Boolean(
        related='company_id.bank_receipt_post_move',
        readonly=False,
    )
