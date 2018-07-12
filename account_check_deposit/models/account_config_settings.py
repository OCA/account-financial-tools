# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    check_deposit_offsetting_account = fields.Selection(
        related='company_id.check_deposit_offsetting_account')
    check_deposit_transfer_account_id = fields.Many2one(
        related='company_id.check_deposit_transfer_account_id')
    check_deposit_post_move = fields.Boolean(
        related='company_id.check_deposit_post_move')
