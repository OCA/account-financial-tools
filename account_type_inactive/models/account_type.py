# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountAccountType(models.Model):

    _inherit = 'account.account.type'

    active = fields.Boolean('Active', default=True)
