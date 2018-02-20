# -*- coding: utf-8 -*-
# © 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import models


class AccountInvoice(models.Model):
    _inherit = ['account.invoice', 'blocked.accounts.mixin']
    _name = 'account.invoice'
    _blocked_accounts_fields = ['account_id']
