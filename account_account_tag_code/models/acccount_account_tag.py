# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAccountTag(models.Model):
    _inherit = 'account.account.tag'

    code = fields.Char()
