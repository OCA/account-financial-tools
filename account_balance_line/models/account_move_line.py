# -*- coding: utf-8 -*-
# Copyright 2010-2014 Camptocamp - Vincent Renaville
# Copyright 2016 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    @api.depends('credit', 'debit')
    def _line_balance(self):
        for line in self:
            line.line_balance = line.debit - line.credit

    line_balance = fields.Float(
        compute='_line_balance', string='Balance', store=True,
        digits=dp.get_precision('Account'))
