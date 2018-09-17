# coding: utf-8
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    group_id = fields.Many2one(
        comodel_name='account.group',
        string="Group",
    )

    @api.onchange('code')
    def onchange_code(self):
        AccountGroup = self.env['account.group']
        group = False
        code_prefix = self.code
        # find group with longest matching prefix
        while code_prefix:
            matching_group = AccountGroup.search([
                ('code_prefix', '=', code_prefix),
            ], limit=1)
            if matching_group:
                group = matching_group
                break
            code_prefix = code_prefix[:-1]
        self.group_id = group
