# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountAccountType(models.Model):

    _inherit = 'account.account.type'
    _order = 'sequence asc'

    sequence = fields.Integer(
        string=u'Sequence',
    )
