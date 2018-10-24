# -*- coding: utf-8 -*-
# Copyright 2018 FIEF Management SA <svalaeys@fiefmanage.ch>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    to_reclassify = fields.Boolean(string='To Reclassify')
