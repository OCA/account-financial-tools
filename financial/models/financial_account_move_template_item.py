# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import UserError
from ..constants import FINANCIAL_MOVE_FIELD


class FinancialAccountMoveTemplateItem(models.Model):
    _name = b'financial.account.move.template.item'
    _description = 'Financial Account Move Template Item'

    template_id = fields.Many2one(
        comodel_name='financial.account.move.template',
        string='Template',
        required=True,
        ondelete='cascade',
    )
    field = fields.Selection(
        selection=FINANCIAL_MOVE_FIELD,
        string='Field',
        required=True,
    )
    account_debit_id = fields.Many2one(
        comodel_name='account.account',
        string='Debit',
    )
    account_credit_id = fields.Many2one(
        comodel_name='account.account',
        string='Credit',
    )
