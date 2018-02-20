# -*- coding: utf-8 -*-
# © 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import models


class AccountInvoiceLine(models.Model):
    _inherit = ['account.invoice.line', 'blocked.accounts.mixin']
    _name = 'account.invoice.line'
    _blocked_accounts_fields = ['account_id', 'account_analytic_id']
