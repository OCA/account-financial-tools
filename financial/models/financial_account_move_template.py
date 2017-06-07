# -*- coding: utf-8 -*-
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import UserError


class FinancialAccountMoveTemplate(models.Model):
    _name = b'financial.account.move.template'
    _description = 'Financial Account Move Template'
    _rec_name = 'name'

    name = fields.Char(
        string='Description',
        required=True,
        index=True,
    )
    parent_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Parent template',
    )
    child_ids = fields.One2many(
        comodel_name='financial.account.move.template',
        inverse_name='parent_id',
        string='Child templates'
    )
    item_ids = fields.One2many(
        comodel_name='financial.account.move.template.item',
        inverse_name='template_id',
        string='Itens',
    )
