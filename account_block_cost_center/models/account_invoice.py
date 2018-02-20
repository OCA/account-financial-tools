# -*- coding: utf-8 -*-
# © 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _register_hook(self, cr):
        self._blocked_accounts_fields.append('cost_center_id')
        return super(AccountInvoice, self)._register_hook(cr)
