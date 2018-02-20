# -*- coding: utf-8 -*-
# © 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import models


class AccountAccount(models.Model):
    _inherit = ['account.account', 'account.block.mixin']
    _name = 'account.account'
