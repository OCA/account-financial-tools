# coding: utf-8
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAccountTemplate(models.Model):
    _inherit = "account.account.template"

    group_id = fields.Many2one(
        comodel_name='account.group',
        string="Group",
    )
