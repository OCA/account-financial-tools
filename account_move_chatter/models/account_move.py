# -*- coding: utf-8 -*-
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = ["account.move", "mail.thread"]
    _name = "account.move"

    state = fields.Selection(track_visibility='always')
