# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountAccount(models.Model):

    _inherit = 'account.account'

    parent_id = fields.Many2one(
        comodel_name='account.account',
        string='Parent account',
        index=True,
    )
