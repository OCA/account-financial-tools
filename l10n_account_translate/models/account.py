# -*- coding: utf-8 -*-
# Copyright 2009-2015 Noviat nv/sa (www.noviat.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    name = fields.Char()
